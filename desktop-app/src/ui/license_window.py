"""
License Activation Window.
"""
import customtkinter as ctk
import threading
import os
from tkinter import messagebox
from PIL import Image

from ..config import Config, get_resource_path
from .components import ModernButton, ModernEntry
from ..license_manager import LicenseManager


class LicenseWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.license_manager = LicenseManager()
        
        # Window setup
        self.title("Activate License")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.configure(fg_color=Config.BG_COLOR)
        
        # Determine logo path (check multiple possible locations)
        self.logo_path = None
        potential_paths = [
            # In development (relative to main.py)
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Logo", "avatar1.ico"),
            # In production (bundled)
            get_resource_path(os.path.join("Logo", "avatar1.ico"))
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                self.logo_path = path
                break
        
        # Set window icon if found
        if self.logo_path:
            try:
                self.iconbitmap(self.logo_path)
            except Exception:
                pass  # Ignore if icon setting fails
        
        self._create_ui()
        
        # Handle close (ensure app exits if window is closed without activation)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _create_ui(self):
        # Center container
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85)
        
        # Logo
        if self.logo_path:
            try:
                # Use CTkImage for better sealing
                pil_image = Image.open(self.logo_path)
                logo_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(100, 100))
                
                logo_label = ctk.CTkLabel(frame, text="", image=logo_img)
                logo_label.pack(pady=(0, 20))
            except Exception as e:
                # Fallback if image loading fails
                print(f"Error loading logo: {e}")
                logo_label = ctk.CTkLabel(frame, text="⚡", font=ctk.CTkFont(size=60))
                logo_label.pack(pady=(0, 20))
        else:
            logo_label = ctk.CTkLabel(frame, text="⚡", font=ctk.CTkFont(size=60))
            logo_label.pack(pady=(0, 20))
            
        # Title
        title = ctk.CTkLabel(
            frame, 
            text=Config.APP_NAME,
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#ffffff"
        )
        title.pack(pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            frame, 
            text="Enterprise Edition",
            font=ctk.CTkFont(size=14),
            text_color=Config.PRIMARY_COLOR
        )
        subtitle.pack(pady=(0, 40))
        
        # License Input
        input_label = ctk.CTkLabel(
            frame, 
            text="Enter License Key",
            font=ctk.CTkFont(size=14),
            text_color="#a0a0a0"
        )
        input_label.pack(anchor="w", pady=(0, 5))
        
        self.key_entry = ModernEntry(frame, placeholder="XXXX-XXXX-XXXX-XXXX")
        self.key_entry.pack(fill="x", pady=(0, 10))
        
        # Hardware ID info
        hw_id = self.license_manager.get_hardware_id()
        hw_label = ctk.CTkLabel(
            frame,
            text=f"Device ID: {hw_id[:8]}...",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        hw_label.pack(pady=(0, 20))
        
        # Activate Button
        self.activate_btn = ModernButton(
            frame,
            text="Activate License",
            command=self._activate,
            style="primary",
            height=40
        )
        self.activate_btn.pack(fill="x", pady=(0, 20))
        
        # Status Label
        self.status_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=Config.WARNING_COLOR
        )
        self.status_label.pack()

    def _activate(self):
        key = self.key_entry.get().strip()
        if not key:
            self.status_label.configure(text="Please enter a license key", text_color=Config.WARNING_COLOR)
            return
            
        self.activate_btn.configure(state="disabled", text="Activating...")
        self.status_label.configure(text="Connecting to server...", text_color="#a0a0a0")
        
        # Run activation in background
        threading.Thread(target=self._activation_thread, args=(key,), daemon=True).start()
        
    def _activation_thread(self, key):
        success, message = self.license_manager.activate_license(key)
        self.after(0, lambda: self._on_activation_complete(success, message))
        
    def _on_activation_complete(self, success, message):
        self.activate_btn.configure(state="normal", text="Activate License")
        
        if success:
            self.status_label.configure(text="Activation Successful!", text_color=Config.SUCCESS_COLOR)
            messagebox.showinfo("Success", "License activated successfully!\nThe application will now start.")
            self.destroy()  # Close license window to allow main app to start
        else:
            self.status_label.configure(text=message, text_color=Config.ERROR_COLOR)
            
    def _on_close(self):
        self.destroy()
        sys.exit(0)  # Exit entire app if closed without activation
