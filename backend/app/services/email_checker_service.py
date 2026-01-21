"""
Email Checker Service - Matches privatedatachecker database schema.

This service checks emails against the existing VPS databases (VPS2-VPS8) using:
- _email_hash field (SHA256 of lowercase email)
- Proper collection routing based on domain/local part
- READ ONLY operations
"""
import hashlib
import re
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import asyncio
from ..core.config import settings


# =============================================================================
# COLLECTION ROUTING LOGIC (matches privatedatachecker/backend/breaches/mongo.py)
# =============================================================================

# Special domain mappings - routes by email local part (username), not domain
VPS5_SPECIAL_DOMAIN_PREFIXES = {
    "yahoo.fr": "YF",
    "comcast.net": "CN",
}

VPS6_SPECIAL_DOMAIN_PREFIXES = {
    "gmail.com": "GC",
}

VPS7_SPECIAL_DOMAIN_PREFIXES = {
    "hotmail.com": "HC",
    "hotmail.fr": "HF",
    "mail.ru": "MR",
}

VPS8_SPECIAL_DOMAIN_PREFIXES = {
    "yahoo.com": "YC",
    "aol.com": "AC",
}

SPECIAL_DOMAIN_PREFIXES = {
    **VPS5_SPECIAL_DOMAIN_PREFIXES,
    **VPS6_SPECIAL_DOMAIN_PREFIXES,
    **VPS7_SPECIAL_DOMAIN_PREFIXES,
    **VPS8_SPECIAL_DOMAIN_PREFIXES,
}


def _normalize_domain(domain: str) -> str:
    """Normalize domain: lowercase, strip protocol/path."""
    if not domain:
        return ""
    domain = re.sub(r'^https?://', '', str(domain).lower().strip())
    domain = domain.split('/')[0].split('?')[0]
    domain = domain.split(':')[0]
    return domain.strip('.')


def _domain_from_email(email: str) -> str:
    """Extract domain from email."""
    if not email or '@' not in str(email):
        return ""
    return _normalize_domain(str(email).split('@')[-1])


def _route_by_local_part(local_part: str, prefix: str) -> str:
    """Route by email local part (username) with a given prefix."""
    if not local_part:
        return f"Email_{prefix}v_{prefix}z_extra"
    
    first = local_part[0].lower()
    if not first.isalpha():
        return f"Email_{prefix}v_{prefix}z_extra"
    
    if 'a' <= first <= 'g':
        return f"Email_{prefix}a_{prefix}g"
    if 'h' <= first <= 'n':
        return f"Email_{prefix}h_{prefix}n"
    if 'o' <= first <= 'u':
        return f"Email_{prefix}o_{prefix}u"
    return f"Email_{prefix}v_{prefix}z_extra"


def _domain_to_collection(domain: str, valid_letters: str) -> Optional[str]:
    """Route domain to collection based on first two letters."""
    d = _normalize_domain(domain)
    if not d:
        return None
    first = d[0].lower()
    if first not in valid_letters:
        return None
    second = d[1].lower() if len(d) > 1 else ""
    upper = first.upper()
    if not second or not second.isalpha():
        return f"Email_{upper}v_{upper}z_extra"
    if 'a' <= second <= 'g':
        return f"Email_{upper}a_{upper}g"
    if 'h' <= second <= 'n':
        return f"Email_{upper}h_{upper}n"
    if 'o' <= second <= 'u':
        return f"Email_{upper}o_{upper}u"
    return f"Email_{upper}v_{upper}z_extra"


def _domain_to_extra_collection(domain: str) -> Optional[str]:
    """Route non-alphabetic domains to Extra collections."""
    d = _normalize_domain(domain)
    if not d:
        return None
    first = d[0].lower()
    if first.isalpha():
        return None
    if first.isdigit():
        digit = int(first)
        if digit <= 3:
            return "Email_Extra1"
        elif digit <= 6:
            return "Email_Extra2"
        else:
            return "Email_Extra3"
    return "Email_Extra_extra"


def get_email_routing(email: str) -> Optional[Dict]:
    """
    Determine which VPS and collection an email should be routed to.
    
    Returns dict with 'vps' and 'collection' keys, or None if no routing applies.
    
    Routing priority:
    1. Special domains (route by email local part):
       - VPS5: yahoo.fr, comcast.net
       - VPS6: gmail.com
       - VPS7: hotmail.com, hotmail.fr, mail.ru
       - VPS8: yahoo.com, aol.com
    2. Domain-based routing (route by domain first letter):
       - VPS2: domains A-G
       - VPS3: domains H-N
       - VPS4: domains O-U
       - VPS5: domains V-Z, Extra (non-alphabetic)
    """
    if not email or '@' not in str(email):
        return None
    
    parts = str(email).lower().split('@')
    if len(parts) != 2:
        return None
    
    local_part = parts[0].strip()
    domain = _normalize_domain(parts[1])
    
    # Check special domains first (highest priority)
    if domain in VPS6_SPECIAL_DOMAIN_PREFIXES:
        prefix = VPS6_SPECIAL_DOMAIN_PREFIXES[domain]
        return {"vps": "VPS6", "collection": _route_by_local_part(local_part, prefix)}
    
    if domain in VPS7_SPECIAL_DOMAIN_PREFIXES:
        prefix = VPS7_SPECIAL_DOMAIN_PREFIXES[domain]
        return {"vps": "VPS7", "collection": _route_by_local_part(local_part, prefix)}
    
    if domain in VPS8_SPECIAL_DOMAIN_PREFIXES:
        prefix = VPS8_SPECIAL_DOMAIN_PREFIXES[domain]
        return {"vps": "VPS8", "collection": _route_by_local_part(local_part, prefix)}
    
    if domain in VPS5_SPECIAL_DOMAIN_PREFIXES:
        prefix = VPS5_SPECIAL_DOMAIN_PREFIXES[domain]
        return {"vps": "VPS5", "collection": _route_by_local_part(local_part, prefix)}
    
    # Check VPS2 (A-G domains)
    col = _domain_to_collection(domain, "abcdefg")
    if col:
        return {"vps": "VPS2", "collection": col}
    
    # Check VPS3 (H-N domains)
    col = _domain_to_collection(domain, "hijklmn")
    if col:
        return {"vps": "VPS3", "collection": col}
    
    # Check VPS4 (O-U domains)
    col = _domain_to_collection(domain, "opqrstu")
    if col:
        return {"vps": "VPS4", "collection": col}
    
    # Check VPS5 (V-Z domains)
    col = _domain_to_collection(domain, "vwxyz")
    if col:
        return {"vps": "VPS5", "collection": col}
    
    # Check VPS5 Extra (non-alphabetic domains)
    col = _domain_to_extra_collection(domain)
    if col:
        return {"vps": "VPS5", "collection": col}
    
    return None


def compute_email_hash(email: str) -> str:
    """Compute SHA256 hash of lowercase email (matches privatedatachecker)."""
    return hashlib.sha256(email.lower().strip().encode('utf-8')).hexdigest()


# =============================================================================
# EMAIL CHECKER SERVICE
# =============================================================================

class EmailCheckerService:
    """
    Service to check emails against external VPS databases.
    All operations are READ ONLY.
    
    Uses _email_hash field lookup with proper collection routing
    to match the privatedatachecker database schema.
    """
    
    def __init__(self):
        self._connections: Dict[str, AsyncIOMotorClient] = {}
        self._databases: Dict[str, AsyncIOMotorDatabase] = {}
    
    def get_vps_configs(self) -> List[Dict]:
        """Get list of enabled VPS configurations."""
        vps_list = []
        
        vps_configs = [
            ("VPS2", settings.VPS2_MONGODB_URL, settings.VPS2_MONGODB_DATABASE, settings.VPS2_ENABLED),
            ("VPS3", settings.VPS3_MONGODB_URL, settings.VPS3_MONGODB_DATABASE, settings.VPS3_ENABLED),
            ("VPS4", settings.VPS4_MONGODB_URL, settings.VPS4_MONGODB_DATABASE, settings.VPS4_ENABLED),
            ("VPS5", settings.VPS5_MONGODB_URL, settings.VPS5_MONGODB_DATABASE, settings.VPS5_ENABLED),
            ("VPS6", settings.VPS6_MONGODB_URL, settings.VPS6_MONGODB_DATABASE, settings.VPS6_ENABLED),
            ("VPS7", settings.VPS7_MONGODB_URL, settings.VPS7_MONGODB_DATABASE, settings.VPS7_ENABLED),
            ("VPS8", settings.VPS8_MONGODB_URL, settings.VPS8_MONGODB_DATABASE, settings.VPS8_ENABLED),
        ]
        
        for name, url, database, enabled in vps_configs:
            if enabled and url:
                vps_list.append({
                    "name": name,
                    "url": url,
                    "database": database
                })
        
        return vps_list
    
    async def connect_to_vps(self, vps_config: Dict) -> Optional[AsyncIOMotorDatabase]:
        """Connect to a single VPS database."""
        try:
            client = AsyncIOMotorClient(
                vps_config["url"],
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Test connection
            await client.admin.command('ping')
            
            self._connections[vps_config["name"]] = client
            self._databases[vps_config["name"]] = client[vps_config["database"]]
            
            print(f"Connected to {vps_config['name']}: {vps_config['database']}")
            return self._databases[vps_config["name"]]
        except Exception as e:
            print(f"Failed to connect to {vps_config['name']}: {e}")
            return None
    
    async def connect_all(self):
        """Connect to all enabled VPS databases."""
        configs = self.get_vps_configs()
        if not configs:
            print("WARNING: No VPS databases configured!")
            return
        
        tasks = [self.connect_to_vps(config) for config in configs]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"Connected to {len(self._databases)} VPS databases: {list(self._databases.keys())}")
    
    def close_all(self):
        """Close all VPS connections."""
        for name, client in self._connections.items():
            try:
                client.close()
            except Exception:
                pass
        self._connections.clear()
        self._databases.clear()
    
    async def check_email_exists(self, email: str) -> bool:
        """
        Check if an email exists in the appropriate VPS database.
        Returns True if email is found (leaked), False otherwise.
        
        Uses _email_hash lookup with proper collection routing.
        """
        # Get routing info for this email
        routing = get_email_routing(email)
        if not routing:
            # No routing means we can't check this email
            print(f"No routing for email domain: {email}")
            return False
        
        vps_name = routing["vps"]
        collection_name = routing["collection"]
        
        # Check if we have this VPS connected
        if vps_name not in self._databases:
            print(f"VPS {vps_name} not connected, cannot check email")
            return False
        
        db = self._databases[vps_name]
        email_hash = compute_email_hash(email)
        
        try:
            result = await db[collection_name].find_one(
                {"_email_hash": email_hash},
                {"_id": 1}
            )
            return result is not None
        except Exception as e:
            print(f"Error checking email in {vps_name}/{collection_name}: {e}")
            return False
    
    async def check_emails_batch(
        self, 
        emails: List[str],
        batch_size: int = 50
    ) -> Dict[str, bool]:
        """
        Check multiple emails in batch.
        Returns dict: {email: is_leaked}
        """
        results = {}
        
        for i in range(0, len(emails), batch_size):
            batch = emails[i:i + batch_size]
            
            # Check each email in the batch concurrently
            tasks = [self.check_email_exists(email) for email in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for email, is_leaked in zip(batch, batch_results):
                if isinstance(is_leaked, Exception):
                    print(f"Error checking {email}: {is_leaked}")
                    results[email] = False
                else:
                    results[email] = is_leaked
        
        return results
    
    async def filter_fresh_emails(self, emails: List[str]) -> List[str]:
        """
        Filter out leaked emails and return only fresh ones.
        """
        check_results = await self.check_emails_batch(emails)
        
        fresh_emails = [
            email for email, is_leaked in check_results.items()
            if not is_leaked
        ]
        
        return fresh_emails


# Singleton instance for use in workers
email_checker = EmailCheckerService()
