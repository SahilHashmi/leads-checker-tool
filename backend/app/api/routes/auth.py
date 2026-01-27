from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...models.schemas import (
    DeviceKeyVerify, 
    DeviceKeyVerifyResponse,
    AdminLogin,
    AdminLoginResponse
)
from ...core.config import settings
from ...core.security import create_access_token, verify_password
from ...services.device_key_service import DeviceKeyService
from ..dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/verify-key", response_model=DeviceKeyVerifyResponse)
async def verify_device_key(
    data: DeviceKeyVerify,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Verify if a device key is valid and active."""
    is_valid = await DeviceKeyService.verify_key(db, data.device_key)
    
    if is_valid:
        return DeviceKeyVerifyResponse(
            valid=True,
            message="Device key is valid"
        )
    else:
        return DeviceKeyVerifyResponse(
            valid=False,
            message="Invalid or inactive device key"
        )


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(data: AdminLogin):
    """Admin login to get access token."""
    if data.email != settings.ADMIN_EMAIL or data.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(
        data={"sub": data.email, "type": "admin"}
    )
    
    return AdminLoginResponse(access_token=access_token)
