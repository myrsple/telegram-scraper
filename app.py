#!/usr/bin/env python3
"""Telegram Scraper - Desktop GUI Application."""

import asyncio
import threading
import os
import sys
from pathlib import Path
from datetime import datetime

# === CRITICAL: Load fonts BEFORE importing tkinter/customtkinter ===
# Tkinter caches available fonts at import time, so we must register fonts first

def _get_fonts_dir():
    """Get the fonts directory, handling both dev and bundled app contexts."""
    # For PyInstaller bundled app
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return base_path / "fonts"

def _register_fonts_coretext(fonts_dir):
    """Register fonts on macOS using CoreText."""
    try:
        import ctypes
        from ctypes import c_void_p, c_bool

        ct = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreText.framework/CoreText')
        cf = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')

        CFURLCreateWithFileSystemPath = cf.CFURLCreateWithFileSystemPath
        CFURLCreateWithFileSystemPath.restype = c_void_p
        CFURLCreateWithFileSystemPath.argtypes = [c_void_p, c_void_p, ctypes.c_int, c_bool]

        CTFontManagerRegisterFontsForURL = ct.CTFontManagerRegisterFontsForURL
        CTFontManagerRegisterFontsForURL.restype = c_bool
        CTFontManagerRegisterFontsForURL.argtypes = [c_void_p, ctypes.c_int, c_void_p]

        CFStringCreateWithCString = cf.CFStringCreateWithCString
        CFStringCreateWithCString.restype = c_void_p
        CFStringCreateWithCString.argtypes = [c_void_p, ctypes.c_char_p, ctypes.c_uint32]

        kCFStringEncodingUTF8 = 0x08000100
        kCFURLPOSIXPathStyle = 0
        kCTFontManagerScopeProcess = 1

        success = False
        for font_file in fonts_dir.glob("*.ttf"):
            font_path = str(font_file).encode('utf-8')
            url_string = CFStringCreateWithCString(None, font_path, kCFStringEncodingUTF8)
            url = CFURLCreateWithFileSystemPath(None, url_string, kCFURLPOSIXPathStyle, False)
            ok = CTFontManagerRegisterFontsForURL(url, kCTFontManagerScopeProcess, None)
            success = success or bool(ok)
        return success
    except Exception:
        return False


def _load_fonts_early():
    """Load fonts before tkinter is imported."""
    fonts_dir = _get_fonts_dir()
    if not fonts_dir.exists():
        return False

    # macOS needs CoreText registration for Tk to see the font
    if sys.platform == "darwin":
        if _register_fonts_coretext(fonts_dir):
            return True

    # Other platforms: try pyglet (cross-platform)
    try:
        import pyglet
        pyglet.options['shadow_window'] = False  # Don't create a window
        for font_file in fonts_dir.glob("*.ttf"):
            pyglet.font.add_file(str(font_file))
        return True
    except Exception:
        return False

# Load fonts NOW, before any tkinter imports
_fonts_loaded = _load_fonts_early()

# Now import tkinter and customtkinter
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter.font as tkfont
from PIL import Image

# Color scheme - Blue accent
COLORS = {
    "bg_dark": "#0a0a0a",
    "bg_card": "#111111",
    "bg_input": "#1a1a1a",
    "accent": "#0000FF",  # Pure blue
    "accent_hover": "#4444FF",
    "accent_dark": "#0000CC",
    "accent_secondary": "#4466FF",  # Lighter blue accent
    "success": "#22c55e",
    "warning": "#FFB800",
    "error": "#FF4757",
    "text": "#ffffff",
    "text_muted": "#71717a",
    "border": "#222222",
}

# Font settings - use Space Grotesk if loaded, otherwise fall back
FONT_FAMILY = "Space Grotesk"


class HoverButton(ctk.CTkButton):
    """Button with hover effect."""
    def __init__(self, master, hover_color=None, **kwargs):
        self.default_color = kwargs.get('fg_color', COLORS["accent"])
        self.hover_color = hover_color or COLORS["accent_hover"]
        super().__init__(master, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event=None):
        self.configure(fg_color=self.hover_color)
    
    def _on_leave(self, event=None):
        self.configure(fg_color=self.default_color)


class StatusIndicator(ctk.CTkFrame):
    """Ackee-style status indicator."""
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        # Vibrant green for ready state
        ready_green = "#00ff88"

        # Use a circular frame instead of unicode character to avoid cropping
        self.dot = ctk.CTkFrame(self, fg_color=ready_green, width=8, height=8, corner_radius=4)
        self.dot.pack(side="left", padx=(0, 8), pady=2)
        self.dot.pack_propagate(False)  # Maintain fixed size

        self.label = ctk.CTkLabel(self, text="Ready", font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=ready_green)
        self.label.pack(side="left", padx=(0, 12))  # Extra padding on right
        self._animating = False

    def set_status(self, text, status="idle"):
        colors = {
            "idle": "#00ff88",  # Vibrant green for ready/idle state
            "running": COLORS["accent"],
            "success": COLORS["success"],
            "error": COLORS["error"],
            "warning": COLORS["warning"],
        }
        color = colors.get(status, "#00ff88")
        self.dot.configure(fg_color=color)
        self.label.configure(text=text, text_color=color)


class ModernEntry(ctk.CTkFrame):
    """Modern input field with label."""
    def __init__(self, master, label, placeholder="", show=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        self.label = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(family=FONT_FAMILY, size=12), 
                                   text_color=COLORS["text_muted"], anchor="w")
        self.label.pack(fill="x", pady=(0, 4))
        
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder, 
                                   fg_color=COLORS["bg_input"], 
                                   border_color=COLORS["border"],
                                   border_width=1,
                                   height=38,
                                   font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                                   show=show)
        self.entry.pack(fill="x")
        
        # Hover effect on entry
        self.entry.bind("<Enter>", lambda e: self.entry.configure(border_color=COLORS["accent"]))
        self.entry.bind("<Leave>", lambda e: self.entry.configure(border_color=COLORS["border"]))
    
    def get(self):
        return self.entry.get()
    
    def insert(self, index, text):
        self.entry.insert(index, text)
    
    def delete(self, start, end):
        self.entry.delete(start, end)


class TelegramScraperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("zocoloco")
        self.geometry("580x780")
        self.minsize(520, 600)
        self.configure(fg_color=COLORS["bg_dark"])
        
        # State
        self.client = None
        self.is_running = False
        self.cancel_requested = False
        self.scrape_count = 0
        
        # Store gradient images to prevent garbage collection
        self._gradient_images = {}

        self._create_gradient_backgrounds()
        self._create_widgets()
        self._load_credentials()
        
        # Bind resize to update gradient positions
        self.bind("<Configure>", self._on_resize)
    
    def _create_gradient_backgrounds(self):
        """Create background image and gradient decorations."""
        try:
            # Get assets directory (handles both dev and bundled app)
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS) / "assets"
            else:
                base_path = Path(__file__).parent / "assets"

            # Load main background image first (bottom layer)
            bg_path = base_path / "bg.png"
            if bg_path.exists():
                bg_img = Image.open(bg_path)
                # Scale to cover window - use larger size to ensure coverage
                bg_size = (1200, 1200)
                bg_img = bg_img.resize(bg_size, Image.Resampling.LANCZOS)
                self._gradient_images['bg'] = ctk.CTkImage(
                    light_image=bg_img,
                    dark_image=bg_img,
                    size=bg_size
                )
                self.bg_label = ctk.CTkLabel(
                    self,
                    image=self._gradient_images['bg'],
                    text="",
                    fg_color="transparent"
                )
                # Center the background
                self.bg_label.place(relx=0.5, rely=0.5, anchor="center")
            
            # Gradient size - large enough to create ambient glow effect
            gradient_size = 600
            
            # Load pink gradient for upper right area (on top of bg)
            pink_path = base_path / "pink.png"
            if pink_path.exists():
                pink_img = Image.open(pink_path)
                pink_img = pink_img.resize((gradient_size, gradient_size), Image.Resampling.LANCZOS)
                self._gradient_images['pink'] = ctk.CTkImage(
                    light_image=pink_img, 
                    dark_image=pink_img,
                    size=(gradient_size, gradient_size)
                )
                self.pink_gradient = ctk.CTkLabel(
                    self, 
                    image=self._gradient_images['pink'], 
                    text="",
                    fg_color="transparent"
                )
                # Position: upper right, partially clipped off the right edge
                self.pink_gradient.place(relx=1.0, rely=0.0, anchor="ne", x=180, y=-150)
            
            # Load blue gradient for lower left area (on top of bg)
            blue_path = base_path / "blue.png"
            if blue_path.exists():
                blue_img = Image.open(blue_path)
                blue_img = blue_img.resize((gradient_size, gradient_size), Image.Resampling.LANCZOS)
                self._gradient_images['blue'] = ctk.CTkImage(
                    light_image=blue_img, 
                    dark_image=blue_img,
                    size=(gradient_size, gradient_size)
                )
                self.blue_gradient = ctk.CTkLabel(
                    self, 
                    image=self._gradient_images['blue'], 
                    text="",
                    fg_color="transparent"
                )
                # Position: lower left, partially clipped off the left edge
                self.blue_gradient.place(relx=0.0, rely=1.0, anchor="sw", x=-180, y=150)
                
        except Exception as e:
            print(f"Could not load gradient backgrounds: {e}")
    
    def _on_resize(self, event=None):
        """Handle window resize to keep gradients properly positioned."""
        # Gradients use relative positioning, so they auto-adjust
        # This handler can be used for additional adjustments if needed
        pass

    def _event_inside_canvas(self, event, canvas):
        widget = self.winfo_containing(event.x_root, event.y_root)
        while widget is not None:
            if widget == canvas:
                return True
            widget = widget.master
        return False

    def _enable_scroll_wheel(self, scroll_frame):
        """Enable mouse wheel scrolling when cursor is over the scroll area."""
        canvas = getattr(scroll_frame, "_parent_canvas", None)
        if canvas is None:
            return

        def on_mousewheel(event):
            if not self._event_inside_canvas(event, canvas):
                return
            if sys.platform == "darwin":
                delta = int(-event.delta)
            elif getattr(event, "delta", 0):
                delta = int(-event.delta / 120)
            else:
                if getattr(event, "num", None) == 4:
                    delta = -1
                elif getattr(event, "num", None) == 5:
                    delta = 1
                else:
                    return
            canvas.yview_scroll(delta, "units")

        self.bind_all("<MouseWheel>", on_mousewheel, add="+")
        self.bind_all("<Button-4>", on_mousewheel, add="+")
        self.bind_all("<Button-5>", on_mousewheel, add="+")
    
    def _create_widgets(self):
        # Scrollable content container
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            bg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_hover"],
            scrollbar_fg_color="transparent",
        )
        scroll_frame.pack(fill="both", expand=True, padx=24, pady=24)
        scroll_frame.lift()
        self._enable_scroll_wheel(scroll_frame)
        
        # Header - Ackee style with logo
        header = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left")
        
        # Load and display zoco.png logo
        try:
            if getattr(sys, 'frozen', False):
                logo_path = Path(sys._MEIPASS) / "assets" / "zoco.png"
            else:
                logo_path = Path(__file__).parent / "assets" / "zoco.png"
            logo_image = ctk.CTkImage(light_image=Image.open(logo_path),
                                       dark_image=Image.open(logo_path),
                                       size=(132, 132))
            logo_label = ctk.CTkLabel(logo_frame, image=logo_image, text="")
            logo_label.pack(side="left", padx=(0, 16))
        except Exception:
            # Fallback if image not found
            logo_mark = ctk.CTkFrame(logo_frame, fg_color=COLORS["accent"], 
                                      width=132, height=132, corner_radius=66)
            logo_mark.pack(side="left", padx=(0, 16))
        
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left")
        ctk.CTkLabel(title_frame, text="zocoloco", 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(title_frame, text="Telegram scraper", 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                     text_color=COLORS["text_muted"]).pack(anchor="w")
        
        # Status indicator in header
        self.status = StatusIndicator(header)
        self.status.pack(side="right", pady=8)
        
        # === Credentials Card ===
        cred_card = self._create_card(scroll_frame, "API credentials")
        
        self.api_id_field = ModernEntry(cred_card, "API ID", "Enter your API ID")
        self.api_id_field.pack(fill="x", pady=(0, 12))
        
        self.api_hash_field = ModernEntry(cred_card, "API hash", "Enter your API hash")
        self.api_hash_field.pack(fill="x", pady=(0, 12))
        
        self.phone_field = ModernEntry(cred_card, "Phone number", "+1234567890")
        self.phone_field.pack(fill="x", pady=(0, 16))
        
        save_row = ctk.CTkFrame(cred_card, fg_color="transparent", height=34)
        save_row.pack(fill="x")
        save_row.pack_propagate(False)
        save_btn = HoverButton(save_row, text="Save credentials", 
                               command=self._save_credentials,
                               fg_color="transparent",
                               hover_color=COLORS["bg_input"],
                               border_width=1,
                               border_color=COLORS["border"],
                               text_color=COLORS["text_muted"],
                               height=34,
                               font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        save_btn.place(relx=0.5, rely=0.0, anchor="n", relwidth=0.5)
        
        # === Scrape Settings Card ===
        settings_card = self._create_card(scroll_frame, "Scrape settings")
        
        self.group_field = ModernEntry(settings_card, "Group", "@groupname or t.me/+invite")
        self.group_field.pack(fill="x", pady=(0, 16))
        
        # Scrape type selector
        type_label = ctk.CTkLabel(settings_card, text="What to scrape", 
                                   font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                                   text_color=COLORS["text_muted"], anchor="w")
        type_label.pack(fill="x", pady=(0, 4))
        
        self.scrape_type = ctk.CTkSegmentedButton(settings_card, 
                                                   values=["Combined", "Members", "Messages"],
                                                   font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                                                   fg_color=COLORS["bg_input"],
                                                   selected_color=COLORS["accent"],
                                                   selected_hover_color=COLORS["accent_hover"],
                                                   text_color=COLORS["text"],
                                                   text_color_disabled=COLORS["text_muted"],
                                                   unselected_color=COLORS["bg_input"],
                                                   unselected_hover_color=COLORS["border"],
                                                   height=36)
        self.scrape_type.set("Messages")
        self.scrape_type.pack(fill="x", pady=(0, 14))
        
        # Two columns for limit and date
        row_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 12))
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=1)
        
        self.limit_field = ModernEntry(row_frame, "Message limit", "All")
        self.limit_field.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        self.since_field = ModernEntry(row_frame, "Since date", "YYYY-MM-DD")
        self.since_field.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        
        self.keywords_field = ModernEntry(settings_card, "Filter keywords", "hack, audit, defi (comma-separated)")
        self.keywords_field.pack(fill="x", pady=(0, 12))
        
        # Output directory
        output_label = ctk.CTkLabel(settings_card, text="Output folder", 
                                     font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                                     text_color=COLORS["text_muted"], anchor="w")
        output_label.pack(fill="x", pady=(0, 4))
        
        output_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        output_row.pack(fill="x")
        
        self.output_entry = ctk.CTkEntry(output_row,
                                          fg_color=COLORS["bg_input"],
                                          border_color=COLORS["border"],
                                          border_width=1,
                                          height=38,
                                          font=ctk.CTkFont(family=FONT_FAMILY, size=13))
        self.output_entry.insert(0, str(Path.home() / "Desktop"))
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        browse_btn = HoverButton(output_row, text="Browse", 
                                  command=self._browse_output,
                                  fg_color="transparent",
                                  hover_color=COLORS["bg_input"],
                                  border_width=1,
                                  border_color=COLORS["border"],
                                  text_color=COLORS["text_muted"],
                                  width=70,
                                  height=38,
                                  font=ctk.CTkFont(family=FONT_FAMILY, size=12))
        browse_btn.pack(side="right")
        
        # === Start/Cancel Button - Ackee style ===
        start_row = ctk.CTkFrame(scroll_frame, fg_color="transparent", height=44)
        start_row.pack(fill="x", pady=(16, 10))
        start_row.pack_propagate(False)
        self.start_btn = HoverButton(start_row, 
                                      text="Start scraping",
                                      command=self._toggle_scrape,
                                      fg_color=COLORS["accent"],
                                      hover_color=COLORS["accent_hover"],
                                      text_color="#ffffff",
                                      height=44,
                                      font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
                                      corner_radius=6)
        self.start_btn.place(relx=0.5, rely=0.0, anchor="n", relwidth=0.5)
        
        # === Progress Counter ===
        self.progress_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent", 
                                            corner_radius=8, height=50)
        self.progress_frame.pack(fill="x", pady=(0, 14))
        self.progress_frame.pack_propagate(False)
        
        progress_inner = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        progress_inner.place(relx=0.5, rely=0.5, anchor="center")
        
        self.progress_label = ctk.CTkLabel(progress_inner, text="Ready to scrape",
                                            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                                            text_color=COLORS["text_muted"])
        self.progress_label.pack(side="left", padx=(0, 10))
        
        self.progress_counter = ctk.CTkLabel(progress_inner, text="",
                                              font=ctk.CTkFont(family=FONT_FAMILY, size=18, weight="bold"),
                                              text_color=COLORS["accent"])
        self.progress_counter.pack(side="left")
        
        # === Activity Log Card ===
        log_card = self._create_card(scroll_frame, "Activity log", expand=True)
        
        self.log_text = ctk.CTkTextbox(log_card, 
                                        fg_color=COLORS["bg_input"],
                                        border_width=0,
                                        font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                                        text_color=COLORS["text_muted"],
                                        height=100)
        self.log_text.pack(fill="both", expand=True)
        self._log("Ready to scrape. Enter your credentials and target group.", "system")
    
    def _create_card(self, parent, title, expand=False):
        """Create a styled card container - transparent background."""
        card = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            bg_color="transparent",
            corner_radius=0,
            border_width=0,
        )
        if expand:
            card.pack(fill="both", expand=True, pady=(0, 0))
        else:
            card.pack(fill="x", pady=(0, 14))
        
        # Card header with accent line
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(14, 10))
        
        # Small accent bar before title
        accent_bar = ctk.CTkFrame(header, fg_color=COLORS["accent"], width=3, height=16, corner_radius=2)
        accent_bar.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(header, text=title, 
                     font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                     text_color=COLORS["text"]).pack(side="left")
        
        # Content area
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=expand, padx=18, pady=14)
        
        return content
    
    def _log(self, message, level="info"):
        """Add message to log with timestamp and color."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        prefixes = {
            "system": "●",
            "info": "→",
            "success": "✓",
            "error": "✗",
            "warning": "!",
        }
        prefix = prefixes.get(level, "→")
        
        self.log_text.insert("end", f"[{timestamp}] {prefix} {message}\n")
        self.log_text.see("end")
    
    def _load_credentials(self):
        """Load credentials from .env file."""
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            try:
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if "=" in line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            if key == "TELEGRAM_API_ID":
                                self.api_id_field.insert(0, value)
                            elif key == "TELEGRAM_API_HASH":
                                self.api_hash_field.insert(0, value)
                            elif key == "TELEGRAM_PHONE":
                                self.phone_field.insert(0, value)
            except Exception:
                pass
    
    def _save_credentials(self):
        """Save credentials to .env file."""
        env_path = Path(__file__).parent / ".env"
        try:
            with open(env_path, "w") as f:
                f.write(f"TELEGRAM_API_ID={self.api_id_field.get()}\n")
                f.write(f"TELEGRAM_API_HASH={self.api_hash_field.get()}\n")
                f.write(f"TELEGRAM_PHONE={self.phone_field.get()}\n")
            self._log("Credentials saved successfully", "success")
            self.status.set_status("Credentials saved", "success")
        except Exception as e:
            self._log(f"Failed to save credentials: {e}", "error")
    
    def _browse_output(self):
        """Open directory picker."""
        directory = filedialog.askdirectory(initialdir=self.output_entry.get())
        if directory:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, directory)
    
    def _toggle_scrape(self):
        """Start or cancel the scraping process."""
        if self.is_running:
            # Cancel requested
            self.cancel_requested = True
            self._log("Cancelling... please wait", "warning")
            self.status.set_status("Cancelling...", "warning")
            self.start_btn.configure(state="disabled", text="Cancelling...")
            return
        
        # Validate inputs
        if not all([self.api_id_field.get(), self.api_hash_field.get(), self.phone_field.get()]):
            messagebox.showerror("Missing Credentials", "Please fill in all API credential fields.")
            return
        
        if not self.group_field.get():
            messagebox.showerror("Missing Group", "Please enter a group to scrape.")
            return
        
        self.is_running = True
        self.cancel_requested = False
        self.scrape_count = 0
        self.start_btn.configure(text="Cancel", fg_color=COLORS["error"],
                                  hover_color="#FF6B6B", text_color="#ffffff")
        self.start_btn.default_color = COLORS["error"]
        self.start_btn.hover_color = "#FF6B6B"
        self.status.set_status("Starting...", "running")
        self._update_progress("Initializing", 0)
        
        # Clear previous log
        self.log_text.delete("1.0", "end")
        self._log("Starting scrape job...", "system")
        
        # Run in background thread
        thread = threading.Thread(target=self._run_scrape, daemon=True)
        thread.start()
    
    def _update_progress(self, label, count):
        """Update the progress counter."""
        self.progress_label.configure(text=label)
        self.progress_counter.configure(text=str(count) if count > 0 else "")
    
    def _run_scrape(self):
        """Run the scrape in a background thread."""
        try:
            asyncio.run(self._async_scrape())
        except Exception as e:
            self.after(0, lambda: self._log(f"Error: {e}", "error"))
            self.after(0, lambda: self.status.set_status("Failed", "error"))
        finally:
            self.after(0, self._scrape_complete)
    
    async def _async_scrape(self):
        """Async scraping logic."""
        from telethon import TelegramClient
        from telethon.errors import SessionPasswordNeededError
        
        from scraper.client import resolve_group, get_group_info
        from scraper.members import scrape_members
        from scraper.messages import scrape_messages, sort_messages, filter_by_keywords
        from scraper.combined import build_combined
        from scraper.exporter import export_members, export_messages, export_combined
        
        api_id = int(self.api_id_field.get())
        api_hash = self.api_hash_field.get()
        phone = self.phone_field.get()
        group = self.group_field.get()
        scrape_type = self.scrape_type.get()
        output_dir = self.output_entry.get()
        
        limit_str = self.limit_field.get().strip()
        limit = int(limit_str) if limit_str and limit_str.isdigit() else None
        
        since_str = self.since_field.get().strip()
        since = None
        if since_str:
            try:
                since = datetime.strptime(since_str, "%Y-%m-%d").date()
            except ValueError:
                self.after(0, lambda: self._log("Invalid date format, ignoring since filter", "warning"))
        
        keywords_str = self.keywords_field.get().strip()
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()] if keywords_str else None
        
        self.after(0, lambda: self._log("Connecting to Telegram...", "info"))
        self.after(0, lambda: self.status.set_status("Connecting...", "running"))
        
        # Create client
        session_path = Path(__file__).parent / "session"
        client = TelegramClient(str(session_path), api_id, api_hash)
        
        try:
            await client.connect()
            
            if not await client.is_user_authorized():
                self.after(0, lambda: self._log("Sending verification code to your Telegram...", "info"))
                self.after(0, lambda: self.status.set_status("Awaiting code...", "warning"))
                await client.send_code_request(phone)
                
                code = await self._ask_for_code()
                if not code:
                    self.after(0, lambda: self._log("Authentication cancelled", "error"))
                    return
                
                try:
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    self.after(0, lambda: self._log("2FA required, please enter password", "warning"))
                    password = await self._ask_for_password()
                    if not password:
                        self.after(0, lambda: self._log("Authentication cancelled", "error"))
                        return
                    await client.sign_in(password=password)
                
                self.after(0, lambda: self._log("Successfully authenticated!", "success"))
            
            # Resolve group
            self.after(0, lambda: self._log(f"Resolving group: {group}", "info"))
            self.after(0, lambda: self.status.set_status("Resolving group...", "running"))
            
            entity = await resolve_group(client, group)
            info = await get_group_info(client, entity)
            
            self.after(0, lambda: self._log(f"Found: {info['title']} ({info['type']})", "success"))
            if info['members_count']:
                self.after(0, lambda: self._log(f"Group has ~{info['members_count']:,} members", "info"))
            
            # Combined export
            if scrape_type == "Combined" and not self.cancel_requested:
                self.after(0, lambda: self._log("Combined export enabled (experimental)", "warning"))
                self.after(0, lambda: self.status.set_status("Scraping combined...", "running"))

                members = await self._scrape_members_with_progress(client, entity)
                messages = await self._scrape_messages_with_progress(client, entity, limit, since)

                if messages and keywords:
                    original = len(messages)
                    messages = filter_by_keywords(messages, keywords)
                    self.after(0, lambda: self._log(f"Keyword filter: {len(messages)}/{original} messages match", "info"))

                combined_rows = build_combined(members, messages)
                if combined_rows:
                    filepath = export_combined(combined_rows, info['title'], output_dir=output_dir)
                    if self.cancel_requested:
                        self.after(0, lambda: self._log(f"Partial export: {len(combined_rows)} rows → {Path(filepath).name}", "warning"))
                    else:
                        self.after(0, lambda: self._log(f"Exported {len(combined_rows)} rows → {Path(filepath).name}", "success"))
                else:
                    self.after(0, lambda: self._log("No combined data found", "warning"))

            # Scrape members
            if scrape_type == "Members" and not self.cancel_requested:
                self.after(0, lambda: self._log("Scraping members (this may take a while)...", "info"))
                self.after(0, lambda: self.status.set_status("Scraping members...", "running"))
                
                members = await self._scrape_members_with_progress(client, entity)
                
                if self.cancel_requested and members:
                    filepath = export_members(members, info['title'], output_dir=output_dir)
                    self.after(0, lambda: self._log(f"Partial export: {len(members)} members → {Path(filepath).name}", "warning"))
                elif members:
                    filepath = export_members(members, info['title'], output_dir=output_dir)
                    self.after(0, lambda: self._log(f"Exported {len(members)} members → {Path(filepath).name}", "success"))
                else:
                    self.after(0, lambda: self._log("No members found or no access", "warning"))
            
            # Scrape messages
            if scrape_type == "Messages" and not self.cancel_requested:
                self.after(0, lambda: self._log("Scraping messages...", "info"))
                self.after(0, lambda: self.status.set_status("Scraping messages...", "running"))
                
                messages = await self._scrape_messages_with_progress(client, entity, limit, since)
                
                if messages:
                    if keywords:
                        original = len(messages)
                        messages = filter_by_keywords(messages, keywords)
                        self.after(0, lambda: self._log(f"Keyword filter: {len(messages)}/{original} messages match", "info"))
                    
                    if messages:
                        messages = sort_messages(messages, chronological=False)
                        filepath = export_messages(messages, info['title'], output_dir=output_dir)
                        if self.cancel_requested:
                            self.after(0, lambda: self._log(f"Partial export: {len(messages)} messages → {Path(filepath).name}", "warning"))
                        else:
                            self.after(0, lambda: self._log(f"Exported {len(messages)} messages → {Path(filepath).name}", "success"))
                    else:
                        self.after(0, lambda: self._log("No messages match keywords", "warning"))
                else:
                    self.after(0, lambda: self._log("No messages found", "warning"))
            
            if self.cancel_requested:
                self.after(0, lambda: self._log("Scrape cancelled. Partial data exported.", "warning"))
                self.after(0, lambda: self.status.set_status("Cancelled", "warning"))
            else:
                self.after(0, lambda: self._log("All done! Check your output folder.", "success"))
                self.after(0, lambda: self.status.set_status("Complete!", "success"))
            
        finally:
            await client.disconnect()
    
    async def _scrape_members_with_progress(self, client, entity):
        """Scrape members with live progress updates."""
        import random
        from telethon.errors import FloodWaitError, ChatAdminRequiredError
        from telethon.tl.types import UserStatusOnline, UserStatusOffline, UserStatusRecently
        from telethon.tl.types import UserStatusLastWeek, UserStatusLastMonth
        from telethon.tl.functions.users import GetFullUserRequest
        
        def extract_last_seen(user):
            status = user.status
            if status is None:
                return None
            if isinstance(status, UserStatusOnline):
                return 'online'
            if isinstance(status, UserStatusOffline):
                return status.was_online.isoformat() if status.was_online else 'offline'
            if isinstance(status, UserStatusRecently):
                return 'recently'
            if isinstance(status, UserStatusLastWeek):
                return 'last_week'
            if isinstance(status, UserStatusLastMonth):
                return 'last_month'
            return 'hidden'
        
        async def get_user_bio(user):
            try:
                full_user = await client(GetFullUserRequest(user))
                return full_user.full_user.about
            except:
                return None
        
        members = []
        count = 0
        
        try:
            async for user in client.iter_participants(entity):
                # Check for cancellation
                if self.cancel_requested:
                    self.after(0, lambda: self._log(f"Cancelled after {count} members", "warning"))
                    break
                
                await asyncio.sleep(random.uniform(0.5, 1.5))
                bio = await get_user_bio(user)
                
                member = {
                    'user_id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'is_bot': user.bot,
                    'last_seen': extract_last_seen(user),
                    'is_premium': getattr(user, 'premium', False),
                    'bio': bio,
                }
                members.append(member)
                count += 1
                
                # Update progress live
                self.after(0, lambda c=count: self._update_progress("Scraping members", c))
                
                if count % 10 == 0:
                    await asyncio.sleep(random.uniform(2, 4))
                if count % 50 == 0:
                    self.after(0, lambda: self._log(f"Scraped {count} members...", "info"))
                    await asyncio.sleep(random.uniform(5, 10))
                    
        except ChatAdminRequiredError:
            self.after(0, lambda: self._log("Admin privileges required for member list", "error"))
        except Exception as e:
            self.after(0, lambda: self._log(f"Error: {e}", "error"))
        
        return members
    
    async def _scrape_messages_with_progress(self, client, entity, limit, since):
        """Scrape messages with live progress updates."""
        import random
        from telethon.errors import FloodWaitError
        from telethon.tl.types import User, MessageFwdHeader
        
        def get_sender_name(sender):
            if sender is None:
                return None
            if isinstance(sender, User):
                parts = [sender.first_name, sender.last_name]
                return ' '.join(p for p in parts if p)
            return getattr(sender, 'title', None)
        
        def get_forward_info(message):
            fwd = message.fwd_from
            if not fwd:
                return None
            if isinstance(fwd, MessageFwdHeader):
                if fwd.from_name:
                    return fwd.from_name
                if fwd.from_id:
                    return str(fwd.from_id)
            return 'forwarded'
        
        messages = []
        count = 0
        
        try:
            async for message in client.iter_messages(entity, limit=limit):
                # Check for cancellation
                if self.cancel_requested:
                    self.after(0, lambda: self._log(f"Cancelled after {count} messages", "warning"))
                    break
                
                msg_date = message.date.date()
                
                if since and msg_date < since:
                    break
                
                sender = await message.get_sender()
                
                msg_data = {
                    'sender_id': message.sender_id,
                    'sender_username': getattr(sender, 'username', None) if sender else None,
                    'sender_name': get_sender_name(sender),
                    'message_id': message.id,
                    'timestamp': message.date.isoformat(),
                    'text': message.message or '',
                    'reply_to_id': message.reply_to_msg_id if message.reply_to else None,
                    'forward_from': get_forward_info(message),
                    'has_media': bool(message.media),
                    'media_type': message.media.__class__.__name__ if message.media else None,
                }
                messages.append(msg_data)
                count += 1
                
                # Update progress live
                self.after(0, lambda c=count: self._update_progress("Scraping messages", c))
                
                if count % 100 == 0:
                    self.after(0, lambda c=count: self._log(f"Scraped {c} messages...", "info"))
                    await asyncio.sleep(random.uniform(1, 3))
                    
        except FloodWaitError as e:
            self.after(0, lambda: self._log(f"Rate limited, waiting {e.seconds}s...", "warning"))
            await asyncio.sleep(e.seconds)
        except Exception as e:
            self.after(0, lambda: self._log(f"Error: {e}", "error"))
        
        return messages
    
    async def _ask_for_code(self):
        """Ask user for verification code."""
        result = [None]
        event = threading.Event()
        
        def ask():
            dialog = ctk.CTkInputDialog(
                text="Enter the verification code sent to your Telegram app:",
                title="Verification Code"
            )
            result[0] = dialog.get_input()
            event.set()
        
        self.after(0, ask)
        event.wait()
        return result[0]
    
    async def _ask_for_password(self):
        """Ask user for 2FA password."""
        result = [None]
        event = threading.Event()
        
        def ask():
            dialog = ctk.CTkInputDialog(
                text="Enter your two-factor authentication password:",
                title="2FA Password"
            )
            result[0] = dialog.get_input()
            event.set()
        
        self.after(0, ask)
        event.wait()
        return result[0]
    
    def _scrape_complete(self):
        """Called when scraping is done."""
        self.is_running = False
        self.cancel_requested = False
        self.start_btn.default_color = COLORS["accent"]
        self.start_btn.hover_color = COLORS["accent_hover"]
        self.start_btn.configure(
            state="normal", 
            text="Start scraping",
            fg_color=COLORS["accent"],
            text_color="#ffffff"
        )
        self._update_progress("Ready to scrape", 0)


def main():
    app = TelegramScraperApp()
    app.mainloop()


if __name__ == "__main__":
    main()
