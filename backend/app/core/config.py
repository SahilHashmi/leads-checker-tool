from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import os
from pathlib import Path

# Get the project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    # Environment Mode
    ENV_MODE: str = "local"  # "local" or "server"
    
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
    
    # External VPS Databases (READ ONLY) - Local URLs
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
    
    # Server VPS URLs (used when ENV_MODE=server)
    SERVER_VPS2_MONGODB_URL: Optional[str] = None
    SERVER_VPS3_MONGODB_URL: Optional[str] = None
    SERVER_VPS4_MONGODB_URL: Optional[str] = None
    SERVER_VPS5_MONGODB_URL: Optional[str] = None
    SERVER_VPS6_MONGODB_URL: Optional[str] = None
    SERVER_VPS7_MONGODB_URL: Optional[str] = None
    SERVER_VPS8_MONGODB_URL: Optional[str] = None
    
    # Admin
    ADMIN_EMAIL: str = "arif.pambudi0191@gmail.com"
    ADMIN_PASSWORD: str = "HIBP123#"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"
    RESULTS_DIR: str = "./results"
    
    def get_vps_url(self, vps_name: str) -> Optional[str]:
        """Get VPS URL based on ENV_MODE."""
        if self.ENV_MODE == "server":
            # Use SERVER_VPS URLs if available
            server_url = getattr(self, f"SERVER_{vps_name}_MONGODB_URL", None)
            if server_url:
                return server_url
        # Fall back to regular VPS URLs
        return getattr(self, f"{vps_name}_MONGODB_URL", None)
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
