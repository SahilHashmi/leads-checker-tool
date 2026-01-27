from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==================== Enums ====================

class DeviceKeyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== Device Key Schemas ====================

class DeviceKeyBase(BaseModel):
    key: str
    status: DeviceKeyStatus = DeviceKeyStatus.ACTIVE


class DeviceKeyCreate(BaseModel):
    pass  # Key is auto-generated


class DeviceKeyResponse(BaseModel):
    id: str
    key: str
    status: DeviceKeyStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeviceKeyVerify(BaseModel):
    device_key: str


class DeviceKeyVerifyResponse(BaseModel):
    valid: bool
    message: str


class DeviceKeyUpdate(BaseModel):
    status: DeviceKeyStatus


# ==================== Fresh Leads Schemas ====================

class FreshLeadBase(BaseModel):
    email: str
    source: str


class FreshLeadCreate(FreshLeadBase):
    task_id: str


class FreshLeadResponse(BaseModel):
    id: str
    email: str
    source: str
    task_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Task Schemas ====================

class TaskCreate(BaseModel):
    filename: str
    total_emails: int


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    filename: str
    total_emails: int
    processed_emails: int
    leaked_count: int
    fresh_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: float  # 0-100
    total_emails: int
    processed_emails: int
    leaked_count: int
    fresh_count: int
    message: str


# ==================== Upload Schemas ====================

class UploadResponse(BaseModel):
    task_id: str
    message: str
    total_emails: int


# ==================== Admin Schemas ====================

class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DateRangeQuery(BaseModel):
    from_date: datetime
    to_date: datetime


class LeadsDownloadResponse(BaseModel):
    total_leads: int
    download_url: str


# ==================== General Schemas ====================

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    success: bool = False
