import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...models.schemas import (
    UploadResponse,
    TaskStatusResponse,
    TaskStatus,
    MessageResponse
)
from ...services.leads_service import LeadsService
from ...workers.tasks import process_leads_task
from ...core.config import settings
from ..dependencies import get_db, verify_device_key

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/upload", response_model=UploadResponse)
async def upload_leads(
    file: UploadFile = File(...),
    device_key: str = Depends(verify_device_key),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload a TXT file with email leads.
    Each email should be on a separate line.
    """
    # Validate file type
    if not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt files are allowed"
        )
    
    # Check file size
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit"
        )
    
    # Parse emails from file
    try:
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        content_str = content.decode('latin-1')
    
    emails = LeadsService.parse_emails_from_file(content_str)
    
    if not emails:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid emails found in the file"
        )
    
    # Create task
    task_id = await LeadsService.create_task(
        db,
        filename=file.filename,
        total_emails=len(emails)
    )
    
    # Queue the processing task
    process_leads_task.delay(task_id, emails, file.filename)
    
    return UploadResponse(
        task_id=task_id,
        message="File uploaded successfully. Processing started.",
        total_emails=len(emails)
    )


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    device_key: str = Depends(verify_device_key),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get the status of a processing task."""
    task = await LeadsService.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Calculate progress
    progress = 0
    if task.total_emails > 0:
        progress = (task.processed_emails / task.total_emails) * 100
    
    # Generate status message
    if task.status == TaskStatus.PENDING:
        message = "Task is queued for processing"
    elif task.status == TaskStatus.PROCESSING:
        message = f"Processing: {task.processed_emails}/{task.total_emails} emails checked"
    elif task.status == TaskStatus.COMPLETED:
        message = f"Completed: {task.fresh_count} fresh leads found, {task.leaked_count} leaked"
    else:
        message = f"Failed: {task.error_message or 'Unknown error'}"
    
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        progress=round(progress, 2),
        total_emails=task.total_emails,
        processed_emails=task.processed_emails,
        leaked_count=task.leaked_count,
        fresh_count=task.fresh_count,
        message=message
    )


@router.get("/download-result/{task_id}")
async def download_result(
    task_id: str,
    device_key: str = Depends(verify_device_key),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Download the result file with fresh leads."""
    task = await LeadsService.get_task(db, task_id)
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is not completed. Current status: {task.status.value}"
        )
    
    # Get result file path
    filepath = LeadsService.get_result_file_path(task_id)
    
    if not filepath or not os.path.exists(filepath):
        # Generate file from database if not exists
        emails = await LeadsService.get_fresh_leads_by_task(db, task_id)
        filepath = LeadsService.save_result_file(task_id, emails)
    
    return FileResponse(
        path=filepath,
        filename=f"fresh_leads_{task_id}.txt",
        media_type="text/plain"
    )
