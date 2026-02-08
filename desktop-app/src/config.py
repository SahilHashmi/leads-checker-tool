"""
Configuration for the Leads Checker Desktop Application.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)


class Config:
    APP_NAME = "Leads Checker Pro"
    APP_VERSION = "1.0.0"
    
    # API Configuration (default, overridden by .env)
    _API_BASE_URL_DEFAULT = "http://localhost:8000/api"
    
    @classmethod
    def get_api_base_url(cls) -> str:
        """Read BACKEND_BASE_URL from .env and append /api."""
        env_path = cls._get_env_file_path()
        env_vars = cls._parse_env_file(env_path)
        backend_url = env_vars.get("BACKEND_BASE_URL", "http://localhost:8000").rstrip("/")
        return f"{backend_url}/api"
    
    # UI Settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    MIN_WIDTH = 900
    MIN_HEIGHT = 600
    
    # Theme Colors (Enterprise Dark Theme)
    PRIMARY_COLOR = "#1a73e8"
    PRIMARY_HOVER = "#1557b0"
    SECONDARY_COLOR = "#2d2d2d"
    BG_COLOR = "#1e1e1e"
    CARD_BG = "#252526"
    TEXT_COLOR = "#ffffff"
    TEXT_SECONDARY = "#a0a0a0"
    SUCCESS_COLOR = "#4caf50"
    WARNING_COLOR = "#ff9800"
    ERROR_COLOR = "#f44336"
    BORDER_COLOR = "#3d3d3d"
    
    # Processing Settings
    BATCH_SIZE = 100
    MAX_CONCURRENT_CHECKS = 50
    CONNECTION_TIMEOUT_MS = 5000
    
    # File Settings
    MAX_FILE_SIZE_MB = 100
    SUPPORTED_EXTENSIONS = ['.txt', '.csv']
    
    # Database Collections Mapping
    VPS_CONFIGS = {
        "VPS2": {"domains": "A-G", "db": "email_A_G"},
        "VPS3": {"domains": "H-N", "db": "email_H_N"},
        "VPS4": {"domains": "O-U", "db": "email_O_U"},
        "VPS5": {"domains": "V-Z", "db": "email_V_Z"},
        "VPS6": {"domains": "gmail.com", "db": "email_gmail"},
        "VPS7": {"domains": "hotmail.com", "db": "email_hotmail"},
        "VPS8": {"domains": "yahoo.com, aol.com", "db": "email_yahoo_aol"},
    }
    
    # .env file path (same as backend - project root)
    @staticmethod
    def _get_env_file_path() -> str:
        """Find the .env file at the project root."""
        # desktop-app/src/config.py -> go up to project root
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller bundled: .env should be next to the exe or in cwd
            candidates = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.path.dirname(sys.executable), '.env'),
            ]
        else:
            # Development: desktop-app/src/config.py -> ../../.env (project root)
            src_dir = os.path.dirname(os.path.abspath(__file__))
            desktop_dir = os.path.dirname(src_dir)
            project_root = os.path.dirname(desktop_dir)
            candidates = [
                os.path.join(project_root, '.env'),
            ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        return ""
    
    @staticmethod
    def _parse_env_file(env_path: str) -> Dict[str, str]:
        """Parse a .env file into a dict of key=value pairs."""
        env_vars = {}
        if not env_path or not os.path.exists(env_path):
            return env_vars
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
        except Exception:
            pass
        return env_vars
    
    @classmethod
    def get_enabled_vps_configs(cls) -> Dict[str, Dict]:
        """Read .env file and return only enabled VPS configurations.
        
        Returns dict like:
        {
            "VPS2": {"url": "mongodb://...", "database": "email_A_G", "domains": "A-G"},
            ...
        }
        """
        env_path = cls._get_env_file_path()
        env_vars = cls._parse_env_file(env_path)
        
        enabled_configs = {}
        vps_names = ["VPS2", "VPS3", "VPS4", "VPS5", "VPS6", "VPS7", "VPS8"]
        
        for vps in vps_names:
            enabled_key = f"{vps}_ENABLED"
            url_key = f"{vps}_MONGODB_URL"
            db_key = f"{vps}_MONGODB_DATABASE"
            
            is_enabled = env_vars.get(enabled_key, "false").lower() in ("true", "1", "yes")
            if not is_enabled:
                continue
            
            url = env_vars.get(url_key, "")
            if not url:
                continue
            
            # Database from .env, fallback to VPS_CONFIGS default
            database = env_vars.get(db_key, cls.VPS_CONFIGS.get(vps, {}).get("db", "email_data"))
            domains = cls.VPS_CONFIGS.get(vps, {}).get("domains", "")
            
            enabled_configs[vps] = {
                "url": url,
                "database": database,
                "domains": domains,
            }
        
        return enabled_configs
