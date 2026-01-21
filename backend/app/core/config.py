from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os
from pathlib import Path

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "leads-checker-tool"
    DEBUG: bool = False
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    
    # MongoDB (New VPS - Main Database)
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "leads_checker"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_WORKER_CONCURRENCY: int = 4
    
    # External VPS Databases (READ ONLY)
    VPS2_MONGODB_URL: Optional[str] = None
    VPS2_MONGODB_DATABASE: str = "email_data"
    VPS2_ENABLED: bool = False
    
    VPS3_MONGODB_URL: Optional[str] = None
    VPS3_MONGODB_DATABASE: str = "email_data"
    VPS3_ENABLED: bool = False
    
    VPS4_MONGODB_URL: Optional[str] = None
    VPS4_MONGODB_DATABASE: str = "email_data"
    VPS4_ENABLED: bool = False
    
    VPS5_MONGODB_URL: Optional[str] = None
    VPS5_MONGODB_DATABASE: str = "email_data"
    VPS5_ENABLED: bool = False
    
    VPS6_MONGODB_URL: Optional[str] = None
    VPS6_MONGODB_DATABASE: str = "email_data"
    VPS6_ENABLED: bool = False
    
    VPS7_MONGODB_URL: Optional[str] = None
    VPS7_MONGODB_DATABASE: str = "email_data"
    VPS7_ENABLED: bool = False
    
    VPS8_MONGODB_URL: Optional[str] = None
    VPS8_MONGODB_DATABASE: str = "email_data"
    VPS8_ENABLED: bool = False
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-this-password"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"
    RESULTS_DIR: str = "./results"
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
