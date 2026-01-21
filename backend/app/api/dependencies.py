from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional
from ..db.mongodb import get_database
from ..core.security import decode_access_token
from ..core.config import settings
from ..services.device_key_service import DeviceKeyService

security = HTTPBearer()


async def get_db() -> AsyncIOMotorDatabase:
    """Dependency to get database instance."""
    return get_database()


async def verify_device_key(
    x_device_key: str = Header(..., alias="X-Device-Key"),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> str:
    """Verify device key from header."""
    is_valid = await DeviceKeyService.verify_key(db, x_device_key)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive device key"
        )
    
    return x_device_key


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify admin JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    if payload.get("type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return payload
