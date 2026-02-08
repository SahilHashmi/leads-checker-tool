"""
Leads Checker Pro - Desktop Application
Enterprise-level email verification tool.
"""
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import MainWindow
from src.ui.license_window import LicenseWindow
from src.license_manager import LicenseManager


def main():
    # check for license
    license_manager = LicenseManager()
    
    # If not licensed, show license window
    if not license_manager.is_licensed():
        # License window will exit app if closed without activation
        # It will destroy itself if activation is successful
        license_app = LicenseWindow()
        license_app.mainloop()
        
        # Re-check after license window closes (in case of activation)
        if not license_manager.is_licensed():
            return

    # If licensed, show main window
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
