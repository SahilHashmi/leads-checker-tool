"""
Main Application Window - Enterprise-level UI.
"""
import customtkinter as ctk
import threading
import os
from tkinter import filedialog, messagebox
from datetime import datetime
from typing import Optional, List
import time

from .components import (
    ModernCard, StatsCard, ModernButton, ModernEntry,
    ModernProgressBar, StatusIndicator, LogViewer
)
from ..config import Config
from ..email_checker import EmailChecker


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        self.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        self.minsize(Config.MIN_WIDTH, Config.MIN_HEIGHT)
        
        # Set icon
        try:
            # Check for icon in multiple locations
            potential_paths = [
                # In development (relative to main.py)
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Logo", "avatar1.ico"),
                # In production (bundled)
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Logo", "avatar1.ico")
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    self.iconbitmap(path)
                    break
        except Exception:
            pass
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure colors
        self.configure(fg_color=Config.BG_COLOR)
        
        # Initialize state
        self.email_checker = EmailChecker()
        self.current_file: Optional[str] = None
        self.emails: List[str] = []
        self.processing = False
        self.cancel_event = threading.Event()
        
        # Database configurations
        self.db_configs = {}
        
        # Build UI
        self._create_layout()
        self._create_header()
        self._create_main_content()
        self._create_footer()
        
        # Auto-connect to databases on startup
        self.after(500, self._auto_connect_databases)
        
        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_layout(self):
        """Create main layout structure."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
    
    def _create_header(self):
        """Create header section."""
        self.header = ctk.CTkFrame(self, fg_color="#252526", height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(1, weight=1)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        self.logo_label = ctk.CTkLabel(
            title_frame,
            text="⚡",
            font=ctk.CTkFont(size=28)
        )
        self.logo_label.pack(side="left", padx=(0, 10))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=Config.APP_NAME,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#ffffff"
        )
        self.title_label.pack(side="left")
        
        # Status indicator
        self.status_indicator = StatusIndicator(self.header, "Not Connected")
        self.status_indicator.grid(row=0, column=1, padx=20, pady=10, sticky="e")
    
    def _auto_connect_databases(self):
        """Automatically connect to all databases using .env config."""
        self.log_viewer.log(f"[{self._get_time()}] Reading VPS configuration from .env...")
        self.status_indicator.set_connected(False, "Connecting...")
        
        # Read enabled VPS configs from .env file
        enabled_configs = Config.get_enabled_vps_configs()
        
        if not enabled_configs:
            self.log_viewer.log(f"[{self._get_time()}] ⚠ No VPS databases enabled in .env file")
            self.status_indicator.set_connected(False, "No VPS Configured")
            return
        
        # Log which VPS are enabled/disabled
        all_vps = ["VPS2", "VPS3", "VPS4", "VPS5", "VPS6", "VPS7", "VPS8"]
        for vps in all_vps:
            if vps in enabled_configs:
                self.log_viewer.log(f"[{self._get_time()}] {vps} ({enabled_configs[vps]['domains']}): Enabled")
            else:
                self.log_viewer.log(f"[{self._get_time()}] {vps}: Disabled/Not configured")
        
        # Build db_configs for EmailChecker
        self.db_configs = {}
        for vps, cfg in enabled_configs.items():
            self.db_configs[vps] = {
                "url": cfg["url"],
                "database": cfg["database"]
            }
        
        self.log_viewer.log(f"[{self._get_time()}] Connecting to {len(self.db_configs)} databases...")
        
        # Connect in background thread
        def connect_thread():
            results = self.email_checker.connect(self.db_configs)
            self.after(0, lambda: self._on_connect_complete(results))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def _create_main_content(self):
        """Create main content area."""
        self.main_content = ctk.CTkFrame(self, fg_color=Config.BG_COLOR, corner_radius=0)
        self.main_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(3, weight=1)
        
        # Stats Row
        stats_frame = ctk.CTkFrame(self.main_content, fg_color="transparent")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.total_card = StatsCard(stats_frame, "Total Emails", "0", "📧", "#1a73e8")
        self.total_card.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.processed_card = StatsCard(stats_frame, "Processed", "0", "⚙️", "#ff9800")
        self.processed_card.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.leaked_card = StatsCard(stats_frame, "Leaked", "0", "🚫", "#f44336")
        self.leaked_card.grid(row=0, column=2, padx=10, sticky="ew")
        
        self.fresh_card = StatsCard(stats_frame, "Fresh", "0", "✅", "#4caf50")
        self.fresh_card.grid(row=0, column=3, padx=(10, 0), sticky="ew")
        
        # File Selection Card
        file_card = ModernCard(self.main_content, "File Selection")
        file_card.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        file_inner = ctk.CTkFrame(file_card, fg_color="transparent")
        file_inner.pack(fill="x", padx=20, pady=(0, 15))
        file_inner.grid_columnconfigure(0, weight=1)
        
        self.file_label = ctk.CTkLabel(
            file_inner,
            text="No file selected",
            font=ctk.CTkFont(size=13),
            text_color="#a0a0a0"
        )
        self.file_label.grid(row=0, column=0, sticky="w")
        
        btn_frame = ctk.CTkFrame(file_inner, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        
        self.browse_btn = ModernButton(
            btn_frame,
            text="Browse",
            command=self._browse_file,
            style="secondary",
            icon="📁",
            width=120
        )
        self.browse_btn.pack(side="left", padx=(0, 10))
        
        self.start_btn = ModernButton(
            btn_frame,
            text="Start Check",
            command=self._start_processing,
            style="success",
            icon="▶️",
            width=140
        )
        self.start_btn.pack(side="left")
        
        # Progress Card
        progress_card = ModernCard(self.main_content, "Progress")
        progress_card.grid(row=2, column=0, sticky="ew", pady=(0, 20))
        
        progress_inner = ctk.CTkFrame(progress_card, fg_color="transparent")
        progress_inner.pack(fill="x", padx=20, pady=(0, 15))
        progress_inner.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ModernProgressBar(progress_inner)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.progress_label = ctk.CTkLabel(
            progress_inner,
            text="Ready to process",
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0"
        )
        self.progress_label.grid(row=1, column=0, sticky="w")
        
        self.cancel_btn = ModernButton(
            progress_inner,
            text="Cancel",
            command=self._cancel_processing,
            style="danger",
            icon="⏹️",
            width=100
        )
        self.cancel_btn.grid(row=1, column=1, sticky="e")
        self.cancel_btn.configure(state="disabled")
        
        # Log Viewer
        log_card = ModernCard(self.main_content, "Activity Log")
        log_card.grid(row=3, column=0, sticky="nsew")
        
        self.log_viewer = LogViewer(log_card)
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.log_viewer.log(f"[{self._get_time()}] {Config.APP_NAME} initialized")
    
    def _create_footer(self):
        """Create footer section."""
        self.footer = ctk.CTkFrame(self, fg_color="#252526", height=40, corner_radius=0)
        self.footer.grid(row=2, column=0, sticky="ew")
        
        # Export button
        self.export_btn = ModernButton(
            self.footer,
            text="Export Fresh Leads",
            command=self._export_results,
            style="primary",
            icon="💾",
            width=180
        )
        self.export_btn.pack(side="right", padx=20, pady=5)
        self.export_btn.configure(state="disabled")
        
        # Version info
        version_label = ctk.CTkLabel(
            self.footer,
            text=f"v{Config.APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        )
        version_label.pack(side="left", padx=20, pady=5)
    
    def _get_time(self) -> str:
        return datetime.now().strftime("%H:%M:%S")
    
    def _connect_databases(self):
        """Connect to all configured databases."""
        self._auto_connect_databases()
    
    def _on_connect_complete(self, results: dict):
        """Handle connection completion."""
        connected = sum(1 for v in results.values() if v)
        total = len(results)
        
        for vps, success in results.items():
            status = "✓ Connected" if success else "✗ Failed"
            self.log_viewer.log(f"[{self._get_time()}] {vps}: {status}")
        
        if connected > 0:
            self.status_indicator.set_connected(True, f"Connected ({connected}/{total})")
            self.log_viewer.log(f"[{self._get_time()}] Successfully connected to {connected} databases")
        else:
            self.status_indicator.set_connected(False, "Connection Failed")
            self.log_viewer.log(f"[{self._get_time()}] Failed to connect to any database")
    
    def _browse_file(self):
        """Open file browser."""
        filetypes = [("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        
        if filepath:
            self.current_file = filepath
            filename = os.path.basename(filepath)
            self.file_label.configure(text=filename, text_color="#ffffff")
            
            # Load and parse emails
            self._load_emails(filepath)
    
    def _load_emails(self, filepath: str):
        """Load emails from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Parse emails
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.emails = list(set(re.findall(email_pattern, content.lower())))
        
        self.total_card.update_value(str(len(self.emails)))
        self.log_viewer.log(f"[{self._get_time()}] Loaded {len(self.emails)} unique emails from file")
    
    def _start_processing(self):
        """Start email checking process."""
        if not self.email_checker.is_connected():
            messagebox.showerror("Error", "No databases connected. Check .env configuration.")
            return
        
        if not self.emails:
            messagebox.showerror("Error", "Please select a file with emails first")
            return
        
        # Warn about failed/offline VPS
        failed = self.email_checker.get_failed_vps()
        if failed:
            self.log_viewer.log(f"[{self._get_time()}] ⚠ Offline VPS: {', '.join(sorted(failed))} - emails for these will be skipped")
        
        self.processing = True
        self.cancel_event.clear()
        
        # Update UI
        self.start_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.export_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_bar.set_color("#1a73e8")
        
        self.processed_card.update_value("0")
        self.leaked_card.update_value("0")
        self.fresh_card.update_value("0")
        
        self.log_viewer.log(f"[{self._get_time()}] Starting email verification...")
        
        # Process in background
        def process_thread():
            start_time = time.time()
            fresh_emails = self.email_checker.filter_fresh_emails(
                self.emails,
                progress_callback=self._update_progress,
                cancel_event=self.cancel_event
            )
            elapsed = time.time() - start_time
            self.after(0, lambda: self._on_processing_complete(fresh_emails, elapsed))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def _update_progress(self, processed: int, total: int, leaked: int, fresh: int, skipped: int = 0):
        """Update progress UI (called from background thread)."""
        def update():
            progress = processed / total if total > 0 else 0
            self.progress_bar.set(progress)
            status_text = f"Processing: {processed:,}/{total:,} emails"
            if skipped > 0:
                status_text += f" (skipped: {skipped:,})"
            self.progress_label.configure(text=status_text)
            self.processed_card.update_value(f"{processed:,}")
            self.leaked_card.update_value(f"{leaked:,}")
            self.fresh_card.update_value(f"{fresh:,}")
        
        self.after(0, update)
    
    def _on_processing_complete(self, fresh_emails: List[str], elapsed: float):
        """Handle processing completion."""
        self.processing = False
        self.fresh_emails = fresh_emails
        
        # Update UI
        self.start_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.export_btn.configure(state="normal")
        
        if self.cancel_event.is_set():
            self.progress_bar.set_color("#ff9800")
            self.progress_label.configure(text="Processing cancelled")
            self.log_viewer.log(f"[{self._get_time()}] Processing cancelled by user")
        else:
            self.progress_bar.set(1.0)
            self.progress_bar.set_color("#4caf50")
            self.progress_label.configure(text=f"Completed in {elapsed:.1f}s")
            self.log_viewer.log(f"[{self._get_time()}] ✓ Processing complete!")
            self.log_viewer.log(f"[{self._get_time()}] Found {len(fresh_emails):,} fresh emails")
        
        # Log any VPS that went down during processing
        failed = self.email_checker.get_failed_vps()
        if failed:
            self.log_viewer.log(f"[{self._get_time()}] ⚠ VPS went offline during processing: {', '.join(sorted(failed))}")
            self.log_viewer.log(f"[{self._get_time()}] Emails routed to offline VPS were skipped (included in fresh output)")
    
    def _cancel_processing(self):
        """Cancel ongoing processing."""
        self.cancel_event.set()
        self.log_viewer.log(f"[{self._get_time()}] Cancelling...")
    
    def _export_results(self):
        """Export fresh emails to file."""
        if not hasattr(self, 'fresh_emails') or not self.fresh_emails:
            messagebox.showinfo("Info", "No fresh emails to export")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"fresh_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                for email in self.fresh_emails:
                    f.write(f"{email}\n")
            
            self.log_viewer.log(f"[{self._get_time()}] Exported {len(self.fresh_emails):,} emails to {os.path.basename(filepath)}")
            messagebox.showinfo("Success", f"Exported {len(self.fresh_emails):,} fresh emails!")
    
    def _on_close(self):
        """Handle window close."""
        if self.processing:
            if not messagebox.askyesno("Confirm", "Processing in progress. Are you sure you want to exit?"):
                return
            self.cancel_event.set()
        
        self.email_checker.disconnect()
        self.destroy()
