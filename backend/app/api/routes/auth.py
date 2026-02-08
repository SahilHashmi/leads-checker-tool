from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...models.schemas import (
    DeviceKeyVerify, 
    DeviceKeyVerifyResponse,
    DeviceKeyActivate,
    DeviceKeyActivateResponse,
    AdminLogin,
    AdminLoginResponse
)
from ...core.config import settings
from ...core.security import create_access_token, verify_password
from ...services.device_key_service import DeviceKeyService
from ..dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/activate-key", response_model=DeviceKeyActivateResponse)
async def activate_device_key(
    data: DeviceKeyActivate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Activate a device key and bind it to a PC's hardware ID."""
    success, message, key = await DeviceKeyService.activate_key(
        db, data.device_key, data.hardware_id
    )
    
    return DeviceKeyActivateResponse(
        success=success,
        message=message,
        key=key
    )


@router.post("/verify-key", response_model=DeviceKeyVerifyResponse)
async def verify_device_key(
    data: DeviceKeyVerify,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Verify if a device key is valid, active, and bound to this PC."""
    is_valid, message = await DeviceKeyService.verify_key(
        db, data.device_key, data.hardware_id
    )
    
    return DeviceKeyVerifyResponse(
        valid=is_valid,
        message=message
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

