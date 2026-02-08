"""
License Manager - Handles license key activation and verification.
"""
import os
import sys
import json
import uuid
import hashlib
import platform
import requests
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from .config import Config


class LicenseManager:
    """Manages license key activation and verification."""
    
    def __init__(self):
        self.license_file = self._get_license_file_path()
        self.api_base_url = Config.get_api_base_url()
    
    def _get_license_file_path(self) -> Path:
        """Get the path to the license file in user's app data."""
        if sys.platform == "win32":
            app_data = os.environ.get("APPDATA", os.path.expanduser("~"))
        else:
            app_data = os.path.expanduser("~/.config")
        
        license_dir = Path(app_data) / "LeadsCheckerPro"
        license_dir.mkdir(parents=True, exist_ok=True)
        
        return license_dir / "license.json"
    
    def get_hardware_id(self) -> str:
        """
        Generate a unique hardware identifier for this PC.
        Uses a combination of machine-specific information.
        """
        # Get MAC address (uuid.getnode returns the hardware address as 48-bit positive integer)
        mac = uuid.getnode()
        
        # Get machine name
        machine_name = platform.node()
        
        # Get processor info
        processor = platform.processor()
        
        # Combine and hash for a consistent ID
        combined = f"{mac}-{machine_name}-{processor}"
        hardware_id = hashlib.sha256(combined.encode()).hexdigest()[:32]
        
        return hardware_id
    
    def get_saved_license(self) -> Optional[str]:
        """Read saved license key from local storage."""
        try:
            if self.license_file.exists():
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("license_key")
        except (json.JSONDecodeError, IOError):
            pass
        return None
    
    def save_license(self, license_key: str) -> bool:
        """Save license key to local storage."""
        try:
            data = {
                "license_key": license_key,
                "hardware_id": self.get_hardware_id()
            }
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            return True
        except IOError:
            return False
    
    def clear_license(self) -> bool:
        """Remove saved license from local storage."""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            return True
        except IOError:
            return False
    
    def activate_license(self, license_key: str) -> Tuple[bool, str]:
        """
        Activate a license key by binding it to this PC's hardware ID.
        Returns (success, message).
        """
        hardware_id = self.get_hardware_id()
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/activate-key",
                json={
                    "device_key": license_key,
                    "hardware_id": hardware_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    # Save license locally on successful activation
                    self.save_license(license_key)
                    return True, data.get("message", "License activated successfully")
                else:
                    return False, data.get("message", "Activation failed")
            else:
                return False, f"Server error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to license server. Check your internet connection."
        except requests.exceptions.Timeout:
            return False, "Connection timeout. Please try again."
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
    
    def verify_license(self, license_key: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verify if the current license is valid.
        Returns (valid, message).
        """
        if license_key is None:
            license_key = self.get_saved_license()
        
        if not license_key:
            return False, "No license key found"
        
        hardware_id = self.get_hardware_id()
        
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/verify-key",
                json={
                    "device_key": license_key,
                    "hardware_id": hardware_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("valid", False), data.get("message", "Unknown status")
            else:
                return False, f"Server error: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to license server"
        except requests.exceptions.Timeout:
            return False, "Connection timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
    
    def is_licensed(self) -> bool:
        """Quick check if a valid license exists."""
        valid, _ = self.verify_license()
        return valid
