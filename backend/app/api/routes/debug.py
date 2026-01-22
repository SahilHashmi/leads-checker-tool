"""
Debug endpoints for troubleshooting VPS email verification issues.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from ...services.email_checker_service import EmailCheckerService, get_email_routing, compute_email_hash
from ...core.config import settings
from ...core.logger import vps_logger, email_checker_logger
import asyncio

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/environment")
async def get_environment_info():
    """Get current environment configuration."""
    return {
        "env_mode": getattr(settings, "ENV_MODE", "not_set"),
        "debug": settings.DEBUG,
        "mongodb_url": settings.MONGODB_URL.replace(settings.MONGODB_URL.split('@')[-1] if '@' in settings.MONGODB_URL else '', '***') if settings.MONGODB_URL else None,
        "mongodb_database": settings.MONGODB_DATABASE,
    }


@router.get("/vps-config")
async def get_vps_configuration():
    """Get VPS database configuration status."""
    checker = EmailCheckerService()
    configs = checker.get_vps_configs()
    
    result = {
        "total_configured": len(configs),
        "vps_databases": []
    }
    
    for config in configs:
        # Mask password in URL for security
        url = config['url']
        if '@' in url:
            parts = url.split('@')
            masked_url = parts[0].split('://')[0] + '://***@' + parts[1]
        else:
            masked_url = url
            
        result["vps_databases"].append({
            "name": config['name'],
            "url": masked_url,
            "database": config['database']
        })
    
    return result


@router.get("/vps-connections")
async def test_vps_connections():
    """Test connections to all VPS databases."""
    checker = EmailCheckerService()
    
    vps_logger.info("=== DEBUG: Testing VPS connections ===")
    
    await checker.connect_all()
    
    result = {
        "total_configured": len(checker.get_vps_configs()),
        "total_connected": len(checker._databases),
        "connected_vps": list(checker._databases.keys()),
        "status": "success" if len(checker._databases) > 0 else "failed",
        "connections": []
    }
    
    for vps_name, db in checker._databases.items():
        try:
            # Test with ping
            await asyncio.wait_for(db.client.admin.command('ping'), timeout=5.0)
            
            # Get collection names
            collections = await asyncio.wait_for(db.list_collection_names(), timeout=5.0)
            
            result["connections"].append({
                "vps": vps_name,
                "database": db.name,
                "status": "connected",
                "collections_count": len(collections),
                "sample_collections": collections[:5] if collections else []
            })
        except Exception as e:
            result["connections"].append({
                "vps": vps_name,
                "database": db.name,
                "status": "error",
                "error": str(e)
            })
    
    checker.close_all()
    
    return result


@router.post("/test-email")
async def test_email_verification(email: str):
    """
    Test email verification for a specific email.
    Shows detailed routing and lookup information.
    """
    email_checker_logger.info(f"=== DEBUG: Testing email verification for: {email} ===")
    
    # Step 1: Get routing info
    routing = get_email_routing(email)
    if not routing:
        return {
            "email": email,
            "status": "no_routing",
            "error": "No routing found for this email domain",
            "routing": None
        }
    
    # Step 2: Compute hash
    email_hash = compute_email_hash(email)
    
    result = {
        "email": email,
        "email_hash": email_hash,
        "routing": routing,
        "vps_connection": None,
        "collection_check": None,
        "is_leaked": False
    }
    
    # Step 3: Connect to VPS
    checker = EmailCheckerService()
    await checker.connect_all()
    
    vps_name = routing["vps"]
    collection_name = routing["collection"]
    
    if vps_name not in checker._databases:
        result["vps_connection"] = {
            "status": "not_connected",
            "required_vps": vps_name,
            "available_vps": list(checker._databases.keys())
        }
        checker.close_all()
        return result
    
    result["vps_connection"] = {
        "status": "connected",
        "vps": vps_name,
        "database": checker._databases[vps_name].name
    }
    
    # Step 4: Check collection
    db = checker._databases[vps_name]
    
    try:
        # Check if collection exists
        collections = await asyncio.wait_for(db.list_collection_names(), timeout=5.0)
        collection_exists = collection_name in collections
        
        result["collection_check"] = {
            "collection": collection_name,
            "exists": collection_exists,
            "total_collections": len(collections)
        }
        
        if not collection_exists:
            result["collection_check"]["error"] = f"Collection {collection_name} not found in database"
            result["collection_check"]["available_collections"] = collections[:10]
            checker.close_all()
            return result
        
        # Step 5: Query for email
        query_result = await asyncio.wait_for(
            db[collection_name].find_one(
                {"_email_hash": email_hash},
                {"_id": 1, "_email_hash": 1}
            ),
            timeout=5.0
        )
        
        result["is_leaked"] = query_result is not None
        result["collection_check"]["query_executed"] = True
        result["collection_check"]["document_found"] = query_result is not None
        
        if query_result:
            result["collection_check"]["document_id"] = str(query_result.get("_id"))
        
        # Get collection stats
        count = await asyncio.wait_for(
            db[collection_name].count_documents({}),
            timeout=5.0
        )
        result["collection_check"]["total_documents"] = count
        
        email_checker_logger.info(f"DEBUG: Email {email} -> {'LEAKED' if result['is_leaked'] else 'FRESH'}")
        
    except Exception as e:
        result["collection_check"] = {
            "collection": collection_name,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    checker.close_all()
    
    return result


@router.post("/test-batch")
async def test_batch_emails(emails: List[str]):
    """Test multiple emails at once."""
    results = []
    
    for email in emails[:10]:  # Limit to 10 emails
        try:
            result = await test_email_verification(email)
            results.append(result)
        except Exception as e:
            results.append({
                "email": email,
                "status": "error",
                "error": str(e)
            })
    
    summary = {
        "total_tested": len(results),
        "leaked_count": sum(1 for r in results if r.get("is_leaked")),
        "fresh_count": sum(1 for r in results if not r.get("is_leaked") and r.get("status") != "error"),
        "error_count": sum(1 for r in results if r.get("status") == "error"),
        "results": results
    }
    
    return summary


@router.get("/logs/recent")
async def get_recent_logs(lines: int = 50):
    """Get recent log entries from all log files."""
    import os
    
    logs_dir = "logs"
    log_files = [
        "vps_connections.log",
        "email_checker.log",
        "worker.log",
        "application.log"
    ]
    
    result = {}
    
    for log_file in log_files:
        log_path = os.path.join(logs_dir, log_file)
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    result[log_file] = ''.join(recent_lines)
            except Exception as e:
                result[log_file] = f"Error reading log: {str(e)}"
        else:
            result[log_file] = "Log file not found"
    
    return result


@router.get("/health-detailed")
async def detailed_health_check():
    """Comprehensive health check with all system status."""
    checker = EmailCheckerService()
    await checker.connect_all()
    
    health = {
        "status": "healthy",
        "environment": {
            "env_mode": getattr(settings, "ENV_MODE", "not_set"),
            "debug": settings.DEBUG,
        },
        "vps_databases": {
            "configured": len(checker.get_vps_configs()),
            "connected": len(checker._databases),
            "connected_list": list(checker._databases.keys()),
            "status": "ok" if len(checker._databases) > 0 else "no_connections"
        },
        "issues": []
    }
    
    # Check for issues
    if len(checker._databases) == 0:
        health["status"] = "unhealthy"
        health["issues"].append({
            "severity": "critical",
            "issue": "No VPS databases connected",
            "solution": "Check VPS database URLs in .env file and ensure databases are accessible"
        })
    
    configs = checker.get_vps_configs()
    if len(configs) == 0:
        health["status"] = "unhealthy"
        health["issues"].append({
            "severity": "critical",
            "issue": "No VPS databases configured",
            "solution": "Configure VPS database URLs in .env file (VPS2_MONGODB_URL, etc.)"
        })
    
    if len(checker._databases) < len(configs):
        health["issues"].append({
            "severity": "warning",
            "issue": f"Only {len(checker._databases)}/{len(configs)} VPS databases connected",
            "solution": "Check logs for connection errors"
        })
    
    checker.close_all()
    
    return health
