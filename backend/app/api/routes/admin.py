import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from ...models.schemas import (
    DeviceKeyResponse,
    DeviceKeyUpdate,
    MessageResponse,
    DeviceKeyStatus
)
from ...services.device_key_service import DeviceKeyService
from ...services.leads_service import LeadsService
from ...core.config import settings
from ..dependencies import get_db, verify_admin_token

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/generate-key", response_model=DeviceKeyResponse)
async def generate_device_key(
    admin: dict = Depends(verify_admin_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Generate a new device key."""
    key = await DeviceKeyService.create_key(db)
    return key


@router.get("/keys", response_model=List[DeviceKeyResponse])
async def list_device_keys(
    admin: dict = Depends(verify_admin_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all device keys."""
    keys = await DeviceKeyService.get_all_keys(db)
    return keys


@router.patch("/keys/{key_id}", response_model=DeviceKeyResponse)
async def update_device_key(
    key_id: str,
    data: DeviceKeyUpdate,
    admin: dict = Depends(verify_admin_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Enable or disable a device key."""
    key = await DeviceKeyService.update_key_status(db, key_id, data.status)
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device key not found"
        )
    
    return key


@router.delete("/keys/{key_id}", response_model=MessageResponse)
async def delete_device_key(
    key_id: str,
    admin: dict = Depends(verify_admin_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a device key."""
    deleted = await DeviceKeyService.delete_key(db, key_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device key not found"
        )
    
    return MessageResponse(message="Device key deleted successfully")


@router.get("/leads-by-date")
async def download_leads_by_date(
    from_date: datetime = Query(..., description="Start date (ISO format)"),
    to_date: datetime = Query(..., description="End date (ISO format)"),
    admin: dict = Depends(verify_admin_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Download fresh leads within a date range."""
    emails = await LeadsService.get_fresh_leads_by_date_range(db, from_date, to_date)
    
    if not emails:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No leads found in the specified date range"
        )
    
    # Create temporary file
    os.makedirs(settings.RESULTS_DIR, exist_ok=True)
    
    filename = f"leads_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}.txt"
    filepath = os.path.join(settings.RESULTS_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for email in emails:
            f.write(f"{email}\n")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/plain"
    )


@router.get("/stats")
async def get_stats(
    admin: dict = Depends(verify_admin_token),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get system statistics."""
    # Count device keys
    total_keys = await db.device_keys.count_documents({})
    active_keys = await db.device_keys.count_documents({"status": DeviceKeyStatus.ACTIVE.value})
    
    # Count leads
    total_leads = await db.fresh_leads.count_documents({})
    
    # Count tasks
    total_tasks = await db.tasks.count_documents({})
    completed_tasks = await db.tasks.count_documents({"status": "completed"})
    
    return {
        "device_keys": {
            "total": total_keys,
            "active": active_keys,
            "inactive": total_keys - active_keys
        },
        "fresh_leads": {
            "total": total_leads
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks
        }
    }
