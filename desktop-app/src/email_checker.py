"""
Email Checker Engine - High-performance email verification against MongoDB databases.
"""
import hashlib
import re
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import threading


# Special domain mappings
VPS5_SPECIAL_DOMAINS = {"yahoo.fr": "YF", "comcast.net": "CN"}
VPS6_SPECIAL_DOMAINS = {"gmail.com": "GC"}
VPS7_SPECIAL_DOMAINS = {"hotmail.com": "HC", "hotmail.fr": "HF", "mail.ru": "MR"}
VPS8_SPECIAL_DOMAINS = {"yahoo.com": "YC", "aol.com": "AC"}

ALL_SPECIAL_DOMAINS = {
    **VPS5_SPECIAL_DOMAINS,
    **VPS6_SPECIAL_DOMAINS,
    **VPS7_SPECIAL_DOMAINS,
    **VPS8_SPECIAL_DOMAINS,
}


def normalize_domain(domain: str) -> str:
    if not domain:
        return ""
    domain = re.sub(r'^https?://', '', str(domain).lower().strip())
    domain = domain.split('/')[0].split('?')[0].split(':')[0]
    return domain.strip('.')


def get_domain_from_email(email: str) -> str:
    if not email or '@' not in str(email):
        return ""
    return normalize_domain(str(email).split('@')[-1])


def route_by_local_part(local_part: str, prefix: str) -> str:
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


def domain_to_collection(domain: str, valid_letters: str) -> Optional[str]:
    d = normalize_domain(domain)
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


def domain_to_extra_collection(domain: str) -> Optional[str]:
    d = normalize_domain(domain)
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
    if not email or '@' not in str(email):
        return None
    parts = str(email).lower().split('@')
    if len(parts) != 2:
        return None
    local_part = parts[0].strip()
    domain = normalize_domain(parts[1])
    
    if domain in VPS6_SPECIAL_DOMAINS:
        prefix = VPS6_SPECIAL_DOMAINS[domain]
        return {"vps": "VPS6", "collection": route_by_local_part(local_part, prefix)}
    if domain in VPS7_SPECIAL_DOMAINS:
        prefix = VPS7_SPECIAL_DOMAINS[domain]
        return {"vps": "VPS7", "collection": route_by_local_part(local_part, prefix)}
    if domain in VPS8_SPECIAL_DOMAINS:
        prefix = VPS8_SPECIAL_DOMAINS[domain]
        return {"vps": "VPS8", "collection": route_by_local_part(local_part, prefix)}
    if domain in VPS5_SPECIAL_DOMAINS:
        prefix = VPS5_SPECIAL_DOMAINS[domain]
        return {"vps": "VPS5", "collection": route_by_local_part(local_part, prefix)}
    
    col = domain_to_collection(domain, "abcdefg")
    if col:
        return {"vps": "VPS2", "collection": col}
    col = domain_to_collection(domain, "hijklmn")
    if col:
        return {"vps": "VPS3", "collection": col}
    col = domain_to_collection(domain, "opqrstu")
    if col:
        return {"vps": "VPS4", "collection": col}
    col = domain_to_collection(domain, "vwxyz")
    if col:
        return {"vps": "VPS5", "collection": col}
    col = domain_to_extra_collection(domain)
    if col:
        return {"vps": "VPS5", "collection": col}
    return None


def compute_email_hash(email: str) -> str:
    return hashlib.sha256(email.lower().strip().encode('utf-8')).hexdigest()


class EmailChecker:
    def __init__(self):
        self._connections: Dict[str, MongoClient] = {}
        self._databases: Dict[str, any] = {}
        self._failed_vps: set = set()
        self._lock = threading.Lock()
        self._connected = False
    
    def connect(self, db_configs: Dict[str, Dict]) -> Dict[str, bool]:
        results = {}
        self._failed_vps.clear()
        for vps_name, config in db_configs.items():
            try:
                client = MongoClient(
                    config["url"],
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000
                )
                client.admin.command('ping')
                self._connections[vps_name] = client
                self._databases[vps_name] = client[config["database"]]
                results[vps_name] = True
            except Exception as e:
                self._failed_vps.add(vps_name)
                results[vps_name] = False
        self._connected = len(self._databases) > 0
        return results
    
    def disconnect(self):
        for client in self._connections.values():
            try:
                client.close()
            except:
                pass
        self._connections.clear()
        self._databases.clear()
        self._failed_vps.clear()
        self._connected = False
    
    def is_connected(self) -> bool:
        return self._connected
    
    def get_connected_count(self) -> int:
        return len(self._databases)
    
    def get_failed_vps(self) -> set:
        return self._failed_vps.copy()
    
    def check_single_email(self, email: str) -> Dict:
        """Check a single email. Returns dict with 'status': 'leaked', 'fresh', or 'skipped'."""
        routing = get_email_routing(email)
        if not routing:
            return {"status": "fresh"}
        vps_name = routing["vps"]
        collection_name = routing["collection"]
        
        # VPS not connected (disabled or failed) - skip, don't count as leaked or fresh
        if vps_name not in self._databases:
            return {"status": "skipped", "vps": vps_name}
        
        db = self._databases[vps_name]
        email_hash = compute_email_hash(email)
        try:
            result = db[collection_name].find_one({"_email_hash": email_hash}, {"_id": 1})
            return {"status": "leaked"} if result is not None else {"status": "fresh"}
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            # VPS went down during processing - mark as failed, skip email
            with self._lock:
                self._failed_vps.add(vps_name)
                if vps_name in self._databases:
                    del self._databases[vps_name]
                if vps_name in self._connections:
                    try:
                        self._connections[vps_name].close()
                    except:
                        pass
                    del self._connections[vps_name]
            return {"status": "skipped", "vps": vps_name}
        except Exception:
            return {"status": "fresh"}
    
    def check_emails_batch(
        self,
        emails: List[str],
        progress_callback: Optional[Callable] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> Dict[str, str]:
        """Check emails in batch. Returns dict of email -> status ('leaked', 'fresh', 'skipped')."""
        results = {}
        total = len(emails)
        processed = 0
        leaked = 0
        fresh = 0
        skipped = 0
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_email = {executor.submit(self.check_single_email, email): email for email in emails}
            
            for future in as_completed(future_to_email):
                if cancel_event and cancel_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                email = future_to_email[future]
                try:
                    result = future.result()
                    status = result.get("status", "fresh")
                    results[email] = status
                    if status == "leaked":
                        leaked += 1
                    elif status == "skipped":
                        skipped += 1
                    else:
                        fresh += 1
                except Exception:
                    results[email] = "fresh"
                    fresh += 1
                
                processed += 1
                if progress_callback and processed % 10 == 0:
                    progress_callback(processed, total, leaked, fresh, skipped)
        
        if progress_callback:
            progress_callback(processed, total, leaked, fresh, skipped)
        
        return results
    
    def filter_fresh_emails(
        self,
        emails: List[str],
        progress_callback: Optional[Callable] = None,
        cancel_event: Optional[threading.Event] = None
    ) -> List[str]:
        """Filter and return fresh emails. Skipped emails (unavailable VPS) are also included."""
        results = self.check_emails_batch(emails, progress_callback, cancel_event)
        return [email for email, status in results.items() if status != "leaked"]
