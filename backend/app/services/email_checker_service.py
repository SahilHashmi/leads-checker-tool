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
from ..core.logger import email_checker_logger, vps_logger


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
            ("VPS2", settings.VPS2_MONGODB_DATABASE, settings.VPS2_ENABLED),
            ("VPS3", settings.VPS3_MONGODB_DATABASE, settings.VPS3_ENABLED),
            ("VPS4", settings.VPS4_MONGODB_DATABASE, settings.VPS4_ENABLED),
            ("VPS5", settings.VPS5_MONGODB_DATABASE, settings.VPS5_ENABLED),
            ("VPS6", settings.VPS6_MONGODB_DATABASE, settings.VPS6_ENABLED),
            ("VPS7", settings.VPS7_MONGODB_DATABASE, settings.VPS7_ENABLED),
            ("VPS8", settings.VPS8_MONGODB_DATABASE, settings.VPS8_ENABLED),
        ]
        
        for name, database, enabled in vps_configs:
            if enabled:
                # Get URL based on ENV_MODE
                url = settings.get_vps_url(name)
                if url:
                    vps_list.append({
                        "name": name,
                        "url": url,
                        "database": database
                    })
        
        return vps_list
    
    async def connect_to_vps(self, vps_config: Dict) -> Optional[AsyncIOMotorDatabase]:
        """Connect to a single VPS database with retry logic."""
        vps_name = vps_config["name"]
        vps_url = vps_config["url"]
        vps_db = vps_config["database"]
        
        vps_logger.info(f"Attempting to connect to {vps_name} at {vps_url}")
        
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                vps_logger.info(f"{vps_name}: Connection attempt {attempt}/{max_retries}")
                
                client = AsyncIOMotorClient(
                    vps_url,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000
                )
                
                # Test connection with ping
                await asyncio.wait_for(
                    client.admin.command('ping'),
                    timeout=10.0
                )
                
                self._connections[vps_name] = client
                self._databases[vps_name] = client[vps_db]
                
                vps_logger.info(f"✓ Successfully connected to {vps_name}: {vps_db}")
                return self._databases[vps_name]
                
            except asyncio.TimeoutError:
                vps_logger.error(f"{vps_name}: Connection timeout on attempt {attempt}/{max_retries}")
                if attempt < max_retries:
                    vps_logger.info(f"{vps_name}: Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                vps_logger.error(f"{vps_name}: Connection failed on attempt {attempt}/{max_retries}: {type(e).__name__}: {str(e)}")
                if attempt < max_retries:
                    vps_logger.info(f"{vps_name}: Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
        
        vps_logger.error(f"✗ Failed to connect to {vps_name} after {max_retries} attempts")
        return None
    
    async def connect_all(self):
        """Connect to all enabled VPS databases."""
        configs = self.get_vps_configs()
        
        if not configs:
            vps_logger.warning("⚠ WARNING: No VPS databases configured! Email verification will not work.")
            vps_logger.warning("Please configure VPS database URLs in .env file (VPS2_MONGODB_URL, etc.)")
            return
        
        vps_logger.info(f"Starting connection to {len(configs)} VPS databases...")
        
        tasks = [self.connect_to_vps(config) for config in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log connection summary
        successful = len(self._databases)
        failed = len(configs) - successful
        
        vps_logger.info("="*60)
        vps_logger.info(f"VPS Connection Summary: {successful}/{len(configs)} successful")
        vps_logger.info(f"Connected VPS databases: {list(self._databases.keys())}")
        
        if failed > 0:
            failed_vps = [cfg['name'] for cfg in configs if cfg['name'] not in self._databases]
            vps_logger.warning(f"Failed VPS databases: {failed_vps}")
            vps_logger.warning("Email verification may be incomplete for some domains!")
        
        vps_logger.info("="*60)
        
        # Check indexes on connected databases
        if successful > 0:
            vps_logger.info("Checking indexes on VPS collections...")
            await self.verify_indexes()
    
    async def verify_indexes(self):
        """Verify that _email_hash indexes exist on VPS collections."""
        for vps_name, db in self._databases.items():
            try:
                # Get a sample collection to check
                collections = await asyncio.wait_for(db.list_collection_names(), timeout=10.0)
                if collections:
                    sample_collection = collections[0]
                    indexes = await asyncio.wait_for(
                        db[sample_collection].index_information(),
                        timeout=10.0
                    )
                    
                    # Check if _email_hash index exists
                    has_email_hash_index = any(
                        '_email_hash' in idx.get('key', [{}])[0] 
                        for idx in indexes.values()
                    )
                    
                    if has_email_hash_index:
                        vps_logger.info(f"✓ {vps_name}: _email_hash index found on {sample_collection}")
                    else:
                        vps_logger.warning(f"⚠️ {vps_name}: No _email_hash index on {sample_collection}")
                        vps_logger.warning(f"   This will cause SLOW queries and TIMEOUTS!")
                        vps_logger.warning(f"   Run: db.{sample_collection}.createIndex({{'_email_hash': 1}})")
                        
            except Exception as e:
                vps_logger.warning(f"{vps_name}: Could not verify indexes: {str(e)}")
    
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
            email_checker_logger.warning(f"No routing found for email domain: {email}")
            return False
        
        vps_name = routing["vps"]
        collection_name = routing["collection"]
        
        # Check if we have this VPS connected
        if vps_name not in self._databases:
            email_checker_logger.error(f"VPS {vps_name} not connected, cannot check email: {email}")
            email_checker_logger.error(f"Required VPS: {vps_name}, Available VPS: {list(self._databases.keys())}")
            return False
        
        db = self._databases[vps_name]
        email_hash = compute_email_hash(email)
        
        try:
            result = await asyncio.wait_for(
                db[collection_name].find_one(
                    {"_email_hash": email_hash},
                    {"_id": 1}
                ),
                timeout=30.0  # Increased from 5s to 30s
            )
            
            is_leaked = result is not None
            email_checker_logger.info(f"Email check: {email} -> {vps_name}/{collection_name} -> {'LEAKED' if is_leaked else 'FRESH'}")
            return is_leaked
            
        except asyncio.TimeoutError:
            email_checker_logger.error(f"⚠️ TIMEOUT (30s) checking email in {vps_name}/{collection_name}: {email}")
            email_checker_logger.error(f"This usually means the collection is missing an index on _email_hash field")
            email_checker_logger.error(f"Query: {{'_email_hash': '{email_hash}'}}")
            # Return False on timeout to avoid treating as leaked
            return False
        except Exception as e:
            email_checker_logger.error(f"Error checking email in {vps_name}/{collection_name}: {type(e).__name__}: {str(e)}")
            email_checker_logger.error(f"Email: {email}, Hash: {email_hash}")
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
