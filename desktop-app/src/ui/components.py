"""
Reusable UI Components for Enterprise Look.
"""
import customtkinter as ctk
from typing import Optional, Callable


class ModernCard(ctk.CTkFrame):
    """A modern card component with shadow effect."""
    
    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color="#252526",
            corner_radius=12,
            border_width=1,
            border_color="#3d3d3d",
            **kwargs
        )
        
        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color="#ffffff"
            )
            self.title_label.pack(anchor="w", padx=20, pady=(15, 10))


class StatsCard(ctk.CTkFrame):
    """Statistics display card."""
    
    def __init__(self, master, title: str, value: str, icon: str = "", color: str = "#1a73e8", **kwargs):
        super().__init__(
            master,
            fg_color="#252526",
            corner_radius=12,
            border_width=1,
            border_color="#3d3d3d",
            **kwargs
        )
        
        self.grid_columnconfigure(0, weight=1)
        
        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=28),
            text_color=color
        )
        self.icon_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#ffffff"
        )
        self.value_label.grid(row=1, column=0, padx=20, pady=0, sticky="w")
        
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13),
            text_color="#a0a0a0"
        )
        self.title_label.grid(row=2, column=0, padx=20, pady=(2, 15), sticky="w")
    
    def update_value(self, value: str):
        self.value_label.configure(text=value)


class ModernButton(ctk.CTkButton):
    """Modern styled button."""
    
    def __init__(self, master, text: str, command: Callable = None, 
                 style: str = "primary", icon: str = "", **kwargs):
        
        colors = {
            "primary": ("#1a73e8", "#1557b0"),
            "success": ("#4caf50", "#388e3c"),
            "danger": ("#f44336", "#c62828"),
            "secondary": ("#3d3d3d", "#4d4d4d"),
        }
        
        fg_color, hover_color = colors.get(style, colors["primary"])
        
        display_text = f"{icon}  {text}" if icon else text
        
        # Get height from kwargs or default to 40
        height = kwargs.pop("height", 40)
        
        super().__init__(
            master,
            text=display_text,
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            corner_radius=8,
            height=height,
            font=ctk.CTkFont(size=14, weight="bold"),
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """Modern styled entry field."""
    
    def __init__(self, master, placeholder: str = "", **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            fg_color="#1e1e1e",
            border_color="#3d3d3d",
            border_width=1,
            corner_radius=8,
            height=40,
            font=ctk.CTkFont(size=13),
            **kwargs
        )


class ModernProgressBar(ctk.CTkFrame):
    """Modern progress bar with percentage label."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=8,
            corner_radius=4,
            fg_color="#3d3d3d",
            progress_color="#1a73e8"
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.progress_bar.set(0)
        
        self.percent_label = ctk.CTkLabel(
            self,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#a0a0a0",
            width=50
        )
        self.percent_label.grid(row=0, column=1)
    
    def set(self, value: float):
        self.progress_bar.set(value)
        self.percent_label.configure(text=f"{int(value * 100)}%")
    
    def set_color(self, color: str):
        self.progress_bar.configure(progress_color=color)


class StatusIndicator(ctk.CTkFrame):
    """Connection status indicator."""
    
    def __init__(self, master, text: str = "Disconnected", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.dot = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color="#f44336"
        )
        self.dot.pack(side="left", padx=(0, 5))
        
        self.label = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=12),
            text_color="#a0a0a0"
        )
        self.label.pack(side="left")
    
    def set_connected(self, connected: bool, text: str = ""):
        color = "#4caf50" if connected else "#f44336"
        default_text = "Connected" if connected else "Disconnected"
        self.dot.configure(text_color=color)
        self.label.configure(text=text or default_text)


class LogViewer(ctk.CTkFrame):
    """Log viewer component."""
    
    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color="#1e1e1e",
            corner_radius=8,
            border_width=1,
            border_color="#3d3d3d",
            **kwargs
        )
        
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color="transparent",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color="#a0a0a0",
            wrap="word"
        )
        self.textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.textbox.configure(state="disabled")
    
    def log(self, message: str, level: str = "info"):
        colors = {
            "info": "#a0a0a0",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336"
        }
        
        self.textbox.configure(state="normal")
        self.textbox.insert("end", f"{message}\n")
        self.textbox.configure(state="disabled")
        self.textbox.see("end")
    
    def clear(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
