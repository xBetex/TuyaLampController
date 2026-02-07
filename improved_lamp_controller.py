#!/usr/bin/env python3
"""
Smart Lamp Controller - Improved Version
Modular architecture with better separation of concerns
Includes ColorMapWindow integration and profile support
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import threading
import logging
import sys
import os
import colorsys
from typing import Optional

# Add smart_lamp_controller paths for imports
_base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_base_dir, 'smart_lamp_controller'))
sys.path.insert(0, os.path.join(_base_dir, 'smart_lamp_controller', 'core'))
sys.path.insert(0, os.path.join(_base_dir, 'smart_lamp_controller', 'utils'))
sys.path.insert(0, os.path.join(_base_dir, 'smart_lamp_controller', 'src'))

# Import modular components
from utils.config import Config
from core.device_manager import DeviceManager
from core.audio_processor import AudioProcessor, AUDIO_AVAILABLE
from core.effects_engine import EffectsEngine
from utils.logger_config import setup_logging, get_logger

# Optional imports for color map window
try:
    from core.color_selection_logic import ColorSelectionLogic, SCREEN_CAPTURE_AVAILABLE
    from core.smart_ambient_processor import SmartAmbientProcessor
    from src.color_history import HIST
    COLOR_MAP_AVAILABLE = True
except ImportError as e:
    print(f"ColorMapWindow dependencies not available: {e}")
    COLOR_MAP_AVAILABLE = False
    SCREEN_CAPTURE_AVAILABLE = False


# =============================================================================
# CONFIGURATION PROFILES
# =============================================================================

PROFILES = {
    "default": {
        "name": "Default",
        "description": "Balanced settings for everyday use",
        "effects": {
            "rainbow_speed": 50,
            "default_brightness": 500,
            "default_temperature": 500
        },
        "color_selection": {
            "min_saturation": 0.5,
            "min_brightness": 0.2,
            "max_brightness": 0.85,
            "prefer_blues": True,
            "avoid_skin_tones": True
        }
    },
    "cinema": {
        "name": "Cinema Mode",
        "description": "Optimized for movie watching - subtle ambient colors",
        "effects": {
            "rainbow_speed": 20,
            "default_brightness": 300,
            "default_temperature": 300  # Warmer
        },
        "color_selection": {
            "min_saturation": 0.4,
            "min_brightness": 0.15,
            "max_brightness": 0.6,  # Dimmer for movies
            "prefer_blues": True,
            "avoid_skin_tones": True
        }
    },
    "gaming": {
        "name": "Gaming Mode",
        "description": "Vibrant colors with fast response",
        "effects": {
            "rainbow_speed": 80,
            "default_brightness": 800,
            "default_temperature": 500
        },
        "color_selection": {
            "min_saturation": 0.6,  # More vivid
            "min_brightness": 0.3,
            "max_brightness": 0.9,
            "prefer_blues": False,  # Accept all vibrant colors
            "avoid_skin_tones": True
        }
    },
    "relax": {
        "name": "Relaxation Mode",
        "description": "Calm, warm colors for relaxation",
        "effects": {
            "rainbow_speed": 15,
            "default_brightness": 400,
            "default_temperature": 200  # Very warm
        },
        "color_selection": {
            "min_saturation": 0.3,
            "min_brightness": 0.2,
            "max_brightness": 0.5,
            "prefer_blues": False,
            "prefer_warm": True,
            "avoid_skin_tones": True
        }
    },
    "work": {
        "name": "Work/Focus Mode",
        "description": "Neutral white light for productivity",
        "effects": {
            "rainbow_speed": 30,
            "default_brightness": 700,
            "default_temperature": 700  # Cool white
        },
        "color_selection": {
            "min_saturation": 0.5,
            "min_brightness": 0.4,
            "max_brightness": 0.8,
            "prefer_blues": True,
            "avoid_skin_tones": True
        }
    },
    "party": {
        "name": "Party Mode",
        "description": "Maximum vibrancy and fast effects",
        "effects": {
            "rainbow_speed": 100,
            "default_brightness": 1000,
            "default_temperature": 500
        },
        "color_selection": {
            "min_saturation": 0.7,
            "min_brightness": 0.4,
            "max_brightness": 0.95,
            "prefer_blues": False,
            "avoid_skin_tones": False
        }
    }
}


# =============================================================================
# COLOR MAP WINDOW (Integrated)
# =============================================================================

class ColorMapWindow:
    """Separate window for color map functionality with live preview"""

    def __init__(self, parent, device_manager, effects_engine):
        self.parent = parent
        self.device_manager = device_manager
        self.effects_engine = effects_engine

        # Check dependencies
        if not COLOR_MAP_AVAILABLE:
            messagebox.showerror(
                "Dependencies Missing",
                "ColorMapWindow requires: mss, pillow, numpy\n"
                "Install with: pip install mss pillow numpy"
            )
            return

        # Initialize color logic
        self.color_logic = ColorSelectionLogic()

        # Initialize smart ambient processor
        self.smart_ambient = SmartAmbientProcessor()
        self.live_mode = False

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Color Map - Ambilight Control")
        self.window.geometry("900x600")
        self.window.resizable(True, True)

        # Make window stay on top initially
        self.window.transient(parent)

        # Setup UI
        self.setup_ui()

        # Initialize state
        self.refresh_timer = None
        self.auto_refresh_var = tk.BooleanVar(value=True)

        # Start auto-refresh
        self.start_auto_refresh()

        # Create color map after window is shown
        self.window.after(200, self.create_color_map)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        """Setup the UI layout"""
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            header_frame,
            text="Color Map - Smart Ambient Lighting",
            font=("Segoe UI", 12, "bold"),
        ).pack(side=tk.LEFT)

        ttk.Button(header_frame, text="Close", command=self.on_close).pack(side=tk.RIGHT)

        # Main content - two columns
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left column - Color map
        left_frame = ttk.LabelFrame(content_frame, text="Color Selection", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Color map canvas
        self.color_map_canvas = tk.Canvas(
            left_frame, width=350, height=250, bg="white", relief="sunken", bd=2
        )
        self.color_map_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.color_map_canvas.bind("<Button-1>", self.on_color_map_click)
        self.color_map_canvas.bind("<B1-Motion>", self.on_color_map_drag)

        # Color map controls
        map_controls = ttk.Frame(left_frame)
        map_controls.pack(fill=tk.X)

        ttk.Button(
            map_controls, text="Custom Color", command=self.choose_custom_color
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            map_controls, text="Auto-Select Best", command=self.select_best_color
        ).pack(side=tk.LEFT)

        # Right column - Preview and controls
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)

        # Screen preview
        preview_frame = ttk.LabelFrame(right_frame, text="Screen Preview", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.preview_canvas = tk.Canvas(
            preview_frame, width=200, height=150, bg="#1a1a1a", relief="sunken", bd=2
        )
        self.preview_canvas.pack(pady=(0, 5))

        # Live preview toggle
        self.live_preview_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            preview_frame,
            text="Live Preview",
            variable=self.live_preview_var,
            command=self.toggle_live_preview
        ).pack()

        # Selected color display
        color_frame = ttk.LabelFrame(right_frame, text="Selected Color", padding="10")
        color_frame.pack(fill=tk.X, pady=(0, 10))

        self.color_display = tk.Label(
            color_frame, text="", bg="#ff0000", height=2, relief="sunken", bd=2
        )
        self.color_display.pack(fill=tk.X, pady=(0, 5))

        self.color_info_var = tk.StringVar(value="#FF0000")
        ttk.Label(
            color_frame,
            textvariable=self.color_info_var,
            font=("Consolas", 11, "bold"),
        ).pack()

        # Dominant colors
        dominant_frame = ttk.LabelFrame(right_frame, text="Screen Accent Colors", padding="10")
        dominant_frame.pack(fill=tk.X, pady=(0, 10))

        self.dominant_colors_frame = ttk.Frame(dominant_frame)
        self.dominant_colors_frame.pack(fill=tk.X)

        # Live mode control
        live_frame = ttk.LabelFrame(right_frame, text="Live Ambient", padding="10")
        live_frame.pack(fill=tk.X, pady=(0, 10))

        self.live_var = tk.BooleanVar(value=False)
        self.live_checkbox = ttk.Checkbutton(
            live_frame,
            text="Enable Live Mode",
            variable=self.live_var,
            command=self.toggle_live_mode,
        )
        self.live_checkbox.pack(fill=tk.X)

        # Apply button
        ttk.Button(
            right_frame,
            text="Apply to Lamp",
            command=self.apply_color,
        ).pack(fill=tk.X, pady=(0, 10))

        # Status
        self.status_var = tk.StringVar(value="Ready - Select a color")
        ttk.Label(
            right_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "italic"),
            foreground="#666666",
        ).pack()

    def create_color_map(self):
        """Create HSV color gradient map"""
        width = self.color_map_canvas.winfo_width() or 350
        height = self.color_map_canvas.winfo_height() or 250

        try:
            from PIL import Image, ImageTk

            img = Image.new("RGB", (width, height))

            for x in range(width):
                for y in range(height):
                    hue = x / width
                    saturation = 1.0 - (y / height) * 0.3
                    value = 1.0 - (y / height) * 0.5

                    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
                    img.putpixel((x, y), (int(r * 255), int(g * 255), int(b * 255)))

            self.color_map_image = ImageTk.PhotoImage(img)
            self.color_map_canvas.create_image(0, 0, anchor=tk.NW, image=self.color_map_image)

        except ImportError:
            # Fallback: simple color blocks
            self._create_simple_color_blocks(width, height)

        # Add selection indicator
        center_x, center_y = width // 2, height // 2
        self.selection_indicator = self.color_map_canvas.create_oval(
            center_x - 8, center_y - 8, center_x + 8, center_y + 8,
            outline="white", width=3, fill="", tags="selection"
        )

        self.update_preview()

    def _create_simple_color_blocks(self, width, height):
        """Fallback color blocks when PIL not available"""
        colors = [
            "#ff0000", "#ff8000", "#ffff00", "#80ff00",
            "#00ff00", "#00ff80", "#00ffff", "#0080ff",
            "#0000ff", "#8000ff", "#ff00ff", "#ff0080"
        ]
        block_width = width // len(colors)

        for i, color in enumerate(colors):
            x1 = i * block_width
            self.color_map_canvas.create_rectangle(
                x1, 0, x1 + block_width, height,
                fill=color, outline=""
            )

    def on_color_map_click(self, event):
        """Handle click on color map"""
        self.update_selection_from_click(event.x, event.y)

    def on_color_map_drag(self, event):
        """Handle drag on color map"""
        self.update_selection_from_click(event.x, event.y)

    def update_selection_from_click(self, x: int, y: int):
        """Update color selection from coordinates"""
        width = self.color_map_canvas.winfo_width() or 350
        height = self.color_map_canvas.winfo_height() or 250

        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))

        # Calculate color from position
        hue = x / width
        saturation = 1.0 - (y / height) * 0.3
        value = 1.0 - (y / height) * 0.5

        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        color = '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))

        # Update logic
        if hasattr(self, 'color_logic'):
            self.color_logic.update_selection(color, (x / width, y / height))

        # Update UI
        self.update_selection_indicator(x, y)
        self.update_color_info(color)

    def update_selection_indicator(self, x: int, y: int):
        """Update selection indicator position"""
        self.color_map_canvas.coords(
            self.selection_indicator, x - 8, y - 8, x + 8, y + 8
        )

    def update_color_info(self, color: str):
        """Update color display"""
        self.color_display.config(bg=color)
        self.color_info_var.set(color.upper())

    def update_preview(self):
        """Update screen preview"""
        if not SCREEN_CAPTURE_AVAILABLE:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                100, 75,
                text="Screen capture\nnot available",
                fill="#666666",
                justify=tk.CENTER
            )
            return

        try:
            self.color_logic.capture_screen_thumbnail()
            thumbnail_tk = self.color_logic.get_screen_thumbnail_tk()

            if thumbnail_tk:
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(100, 75, image=thumbnail_tk)
                self.preview_canvas.thumbnail_ref = thumbnail_tk

            self.update_dominant_colors()

        except Exception as e:
            self.status_var.set(f"Preview error: {e}")

    def update_dominant_colors(self):
        """Update dominant colors display"""
        for widget in self.dominant_colors_frame.winfo_children():
            widget.destroy()

        if not hasattr(self, 'color_logic'):
            return

        dominant_colors = self.color_logic.get_dominant_colors(6)

        if dominant_colors:
            for i, (color, percentage) in enumerate(dominant_colors):
                frame = ttk.Frame(self.dominant_colors_frame)
                frame.pack(side=tk.LEFT, padx=2)

                btn = tk.Button(
                    frame, text="", bg=color, width=3, height=1,
                    command=lambda c=color: self.select_dominant_color(c)
                )
                btn.pack()

                ttk.Label(frame, text=f"{percentage:.0f}%", font=("Segoe UI", 7)).pack()
        else:
            ttk.Label(
                self.dominant_colors_frame,
                text="No colorful colors found",
                font=("Segoe UI", 8)
            ).pack()

    def select_dominant_color(self, color: str):
        """Select a dominant color"""
        if hasattr(self, 'color_logic'):
            self.color_logic.update_selection(color, self.color_logic.selected_position)
        self.update_color_info(color)

        # Update indicator position
        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255
            h, s, v = colorsys.rgb_to_hsv(r, g, b)

            width = self.color_map_canvas.winfo_width() or 350
            height = self.color_map_canvas.winfo_height() or 250
            x = int(h * width)
            y = int((1 - v * 0.5) * height)
            self.update_selection_indicator(x, y)
        except Exception:
            pass

    def select_best_color(self):
        """Auto-select the best ambient color"""
        if not hasattr(self, 'color_logic'):
            return

        dominant_colors = self.color_logic.get_dominant_colors(10)

        if not dominant_colors:
            self.status_var.set("No suitable colors found")
            return

        best_color = self.color_logic.get_best_ambient_color(dominant_colors)

        if best_color:
            self.select_dominant_color(best_color)
            percentage = next((p for c, p in dominant_colors if c == best_color), 0)
            self.status_var.set(f"Auto-selected: {best_color} ({percentage:.1f}%)")
        else:
            self.status_var.set("No suitable colors found")

    def choose_custom_color(self):
        """Open color chooser"""
        color = colorchooser.askcolor(title="Choose Color")
        if color and color[1]:
            self.update_color_info(color[1])
            if hasattr(self, 'color_logic'):
                self.color_logic.update_selection(color[1], (0.5, 0.5))

    def apply_color(self):
        """Apply selected color to lamp"""
        if not self.device_manager.is_connected:
            self.status_var.set("Not connected to lamp!")
            return

        color = self.color_info_var.get()

        try:
            self.effects_engine.stop_all_effects()
            self.effects_engine.set_color_from_hex(color, 1.0)
            self.status_var.set(f"Applied {color}")
        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def toggle_live_mode(self):
        """Toggle live ambient mode"""
        if self.live_var.get():
            self.start_live_mode()
        else:
            self.stop_live_mode()

    def start_live_mode(self):
        """Start live ambient lighting"""
        if not self.device_manager.is_connected:
            self.status_var.set("Connect lamp first!")
            self.live_var.set(False)
            return

        self.live_mode = True
        success = self.smart_ambient.start(
            color_callback=self.on_live_color_update,
            status_callback=lambda s: self.status_var.set(s)
        )

        if success:
            self.effects_engine.stop_all_effects()
            self.status_var.set("Live mode active")
        else:
            self.live_mode = False
            self.live_var.set(False)
            self.status_var.set("Failed to start live mode")

    def stop_live_mode(self):
        """Stop live ambient lighting"""
        if self.smart_ambient.is_running():
            self.smart_ambient.stop()
        self.live_mode = False
        self.status_var.set("Live mode stopped")

    def on_live_color_update(self, color: str):
        """Handle live color updates"""
        self.window.after(0, lambda: self._apply_live_color(color))

    def _apply_live_color(self, color: str):
        """Apply live color update"""
        try:
            self.effects_engine.set_color_from_hex(color, 1.0)
            self.update_color_info(color)
        except Exception:
            pass

    def toggle_live_preview(self):
        """Toggle live preview refresh"""
        if self.live_preview_var.get():
            self.start_auto_refresh()
        else:
            if self.refresh_timer:
                self.window.after_cancel(self.refresh_timer)
                self.refresh_timer = None

    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        if self.live_preview_var.get():
            self.update_preview()
            self.refresh_timer = self.window.after(1000, self.start_auto_refresh)

    def on_close(self):
        """Handle window close"""
        if self.live_mode:
            self.stop_live_mode()
        if self.refresh_timer:
            self.window.after_cancel(self.refresh_timer)
        self.window.destroy()


# =============================================================================
# MAIN APPLICATION
# =============================================================================

class LampControllerUI:
    """Main UI class for the Smart Lamp Controller"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = get_logger(__name__)

        # Initialize configuration
        self.config = Config()
        self.current_profile = "default"

        # Setup logging
        setup_logging(log_level="INFO", log_file="logs/lamp_controller.log")

        # Initialize core components
        self.device_manager = DeviceManager(
            self.config.device_config,
            self.config.data_points
        )
        self.audio_processor = AudioProcessor(self.config.audio_config)
        self.effects_engine = EffectsEngine(
            self.device_manager,
            self.audio_processor
        )

        # Color map window reference
        self.color_map_window = None

        # Setup UI
        self.setup_ui()
        self.setup_callbacks()

        # Apply default profile
        self.apply_profile("default")

        # Start connection
        self.connect_to_device()

        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.logger.info("Lamp Controller UI initialized")

    def setup_ui(self):
        """Setup the main UI layout"""
        # Window configuration
        self.root.title(f"Smart Lamp Controller - {self.config.get('device.name')}")
        self.root.geometry(
            f"{self.config.get('ui.window_width', 650)}x{self.config.get('ui.window_height', 750)}"
        )

        # Main container
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.setup_status_bar(main_frame)

        # Profile selection
        self.setup_profile_selection(main_frame)

        # Power controls
        self.setup_power_controls(main_frame)

        # Mode selection
        self.setup_mode_selection(main_frame)

        # Tabbed interface
        self.setup_tabs(main_frame)

        self.logger.info("UI setup completed")

    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(status_frame, text="Status:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Initializing...")
        ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 9)).pack(side=tk.LEFT, padx=(5, 0))

    def setup_profile_selection(self, parent):
        """Setup profile selection dropdown"""
        profile_frame = ttk.LabelFrame(parent, text="Profile", padding="10")
        profile_frame.pack(fill=tk.X, pady=5)

        profile_row = ttk.Frame(profile_frame)
        profile_row.pack(fill=tk.X)

        ttk.Label(profile_row, text="Active Profile:").pack(side=tk.LEFT)

        self.profile_var = tk.StringVar(value="default")
        profile_names = [PROFILES[p]["name"] for p in PROFILES]
        self.profile_combo = ttk.Combobox(
            profile_row,
            textvariable=self.profile_var,
            values=profile_names,
            state="readonly",
            width=20
        )
        self.profile_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.profile_combo.set(PROFILES["default"]["name"])
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)

        # Profile description
        self.profile_desc_var = tk.StringVar(value=PROFILES["default"]["description"])
        ttk.Label(
            profile_frame,
            textvariable=self.profile_desc_var,
            font=("Arial", 8, "italic"),
            foreground="#666666"
        ).pack(anchor=tk.W, pady=(5, 0))

    def setup_power_controls(self, parent):
        """Setup power control buttons"""
        power_frame = ttk.LabelFrame(parent, text="Power Control", padding="10")
        power_frame.pack(fill=tk.X, pady=5)

        btn_frame = ttk.Frame(power_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame, text="Turn ON", command=self.device_manager.turn_on
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        ttk.Button(
            btn_frame, text="Turn OFF", command=self.device_manager.turn_off
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

    def setup_mode_selection(self, parent):
        """Setup light mode selection"""
        mode_frame = ttk.LabelFrame(parent, text="Light Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)

        self.mode_var = tk.StringVar(value="white")
        mode_btn_frame = ttk.Frame(mode_frame)
        mode_btn_frame.pack(fill=tk.X)

        ttk.Radiobutton(
            mode_btn_frame, text="White Light", variable=self.mode_var,
            value="white", command=self.on_mode_change
        ).pack(side=tk.LEFT, padx=10)

        ttk.Radiobutton(
            mode_btn_frame, text="Color Light", variable=self.mode_var,
            value="colour", command=self.on_mode_change
        ).pack(side=tk.LEFT, padx=10)

    def setup_tabs(self, parent):
        """Setup tabbed interface"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        self.setup_white_tab()
        self.setup_color_tab()
        self.setup_effects_tab()

        if AUDIO_AVAILABLE:
            self.setup_audio_tab()

        if COLOR_MAP_AVAILABLE:
            self.setup_ambilight_tab()

    def setup_white_tab(self):
        """Setup white light control tab"""
        white_frame = ttk.Frame(self.notebook)
        self.notebook.add(white_frame, text="White Light")

        content = ttk.Frame(white_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)

        # Brightness control
        bright_frame = ttk.LabelFrame(content, text="Brightness", padding="10")
        bright_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(bright_frame, text="Brightness Level").pack(anchor=tk.W)

        self.brightness_var = tk.DoubleVar(value=self.config.get('effects.default_brightness', 500))
        self.bright_slider = ttk.Scale(
            bright_frame, from_=10, to=1000,
            variable=self.brightness_var, orient=tk.HORIZONTAL
        )
        self.bright_slider.pack(fill=tk.X, pady=(5, 0))
        self.bright_slider.bind("<ButtonRelease-1>", self.on_brightness_change)

        # Temperature control
        temp_frame = ttk.LabelFrame(content, text="Color Temperature", padding="10")
        temp_frame.pack(fill=tk.X)

        ttk.Label(temp_frame, text="Temperature (Warm - Cool)").pack(anchor=tk.W)

        self.temp_var = tk.DoubleVar(value=self.config.get('effects.default_temperature', 500))
        self.temp_slider = ttk.Scale(
            temp_frame, from_=0, to=1000,
            variable=self.temp_var, orient=tk.HORIZONTAL
        )
        self.temp_slider.pack(fill=tk.X, pady=(5, 0))
        self.temp_slider.bind("<ButtonRelease-1>", self.on_temp_change)

    def setup_color_tab(self):
        """Setup static color control tab"""
        color_frame = ttk.Frame(self.notebook)
        self.notebook.add(color_frame, text="Static Color")

        content = ttk.Frame(color_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)

        # Intensity control
        intensity_frame = ttk.LabelFrame(content, text="Color Intensity", padding="10")
        intensity_frame.pack(fill=tk.X, pady=(0, 10))

        self.color_bright_var = tk.DoubleVar(value=1000)
        ttk.Scale(
            intensity_frame, from_=10, to=1000,
            variable=self.color_bright_var, orient=tk.HORIZONTAL
        ).pack(fill=tk.X)

        # Color picker
        picker_frame = ttk.LabelFrame(content, text="Color Selection", padding="10")
        picker_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            picker_frame, text="Choose Color", command=self.choose_color
        ).pack(fill=tk.X, pady=(0, 10))

        self.color_preview = tk.Label(
            picker_frame, text="Current Color", bg="#888888", height=3, relief="sunken"
        )
        self.color_preview.pack(fill=tk.X)

    def setup_effects_tab(self):
        """Setup effects control tab"""
        effects_frame = ttk.Frame(self.notebook)
        self.notebook.add(effects_frame, text="Effects")

        content = ttk.Frame(effects_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)

        # Rainbow effect
        rainbow_frame = ttk.LabelFrame(content, text="Rainbow Effect", padding="10")
        rainbow_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(rainbow_frame, text="Speed").pack(anchor=tk.W)

        self.rainbow_speed_var = tk.DoubleVar(value=self.config.get('effects.rainbow_speed', 50))
        ttk.Scale(
            rainbow_frame, from_=1, to=100,
            variable=self.rainbow_speed_var, orient=tk.HORIZONTAL
        ).pack(fill=tk.X, pady=(5, 10))

        # Hue range
        ttk.Label(rainbow_frame, text="Hue Range (Min-Max)").pack(anchor=tk.W)

        range_frame = ttk.Frame(rainbow_frame)
        range_frame.pack(fill=tk.X)

        self.rainbow_h_min = tk.DoubleVar(value=0.0)
        self.rainbow_h_max = tk.DoubleVar(value=1.0)

        ttk.Scale(range_frame, from_=0.0, to=1.0, variable=self.rainbow_h_min, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Scale(range_frame, from_=0.0, to=1.0, variable=self.rainbow_h_max, orient=tk.HORIZONTAL).pack(fill=tk.X)

        self.rainbow_btn = ttk.Button(
            rainbow_frame, text="Start Rainbow", command=self.toggle_rainbow
        )
        self.rainbow_btn.pack(fill=tk.X, pady=(10, 0))

    def setup_audio_tab(self):
        """Setup audio synchronization tab"""
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="Music Sync")

        content = ttk.Frame(audio_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)

        # Audio mode
        mode_frame = ttk.LabelFrame(content, text="Audio Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        self.audio_mode = tk.StringVar(value="rms_both")
        modes = [
            ("rms_both", "Volume -> Brightness + Color"),
            ("beat_color", "Beat Detection -> Color"),
        ]

        for value, text in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.audio_mode, value=value).pack(anchor=tk.W)

        # Sync control
        self.mic_btn = ttk.Button(
            content, text="Start Music Sync", command=self.toggle_audio_sync
        )
        self.mic_btn.pack(fill=tk.X)

    def setup_ambilight_tab(self):
        """Setup ambilight/color map tab"""
        ambilight_frame = ttk.Frame(self.notebook)
        self.notebook.add(ambilight_frame, text="Ambilight")

        content = ttk.Frame(ambilight_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            content,
            text="Control ambient lighting based on screen content",
            font=("Arial", 9)
        ).pack(pady=(0, 15))

        ttk.Button(
            content,
            text="Open Color Map Window",
            command=self.open_color_map_window
        ).pack(fill=tk.X, pady=(0, 10))

        # Quick controls
        quick_frame = ttk.LabelFrame(content, text="Quick Controls", padding="10")
        quick_frame.pack(fill=tk.X)

        ttk.Button(
            quick_frame,
            text="Start Smart Ambient",
            command=self.start_smart_ambient
        ).pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            quick_frame,
            text="Stop Ambient",
            command=self.stop_smart_ambient
        ).pack(fill=tk.X)

    def setup_callbacks(self):
        """Setup callbacks between components"""
        self.device_manager.add_status_callback(self.on_device_status)
        self.device_manager.add_connection_callback(self.on_connection_change)
        self.effects_engine.add_color_callback(self.on_color_change)

    def connect_to_device(self):
        """Connect to the lamp device"""
        def connect_thread():
            success = self.device_manager.connect()
            if success:
                self.logger.info("Connected to device")
            else:
                self.logger.error("Failed to connect")

        threading.Thread(target=connect_thread, daemon=True).start()

    # ==========================================================================
    # PROFILE MANAGEMENT
    # ==========================================================================

    def on_profile_change(self, event=None):
        """Handle profile selection change"""
        selected_name = self.profile_var.get()

        # Find profile key by name
        for key, profile in PROFILES.items():
            if profile["name"] == selected_name:
                self.apply_profile(key)
                break

    def apply_profile(self, profile_key: str):
        """Apply a profile's settings"""
        if profile_key not in PROFILES:
            return

        profile = PROFILES[profile_key]
        self.current_profile = profile_key

        # Update UI
        self.profile_desc_var.set(profile["description"])

        # Apply effect settings
        effects = profile["effects"]
        self.rainbow_speed_var.set(effects["rainbow_speed"])
        self.brightness_var.set(effects["default_brightness"])
        self.temp_var.set(effects["default_temperature"])

        # Apply to device if connected
        if self.device_manager.is_connected:
            self.device_manager.set_brightness(int(effects["default_brightness"]))
            self.device_manager.set_temperature(int(effects["default_temperature"]))

        self.status_var.set(f"Profile: {profile['name']}")
        self.logger.info(f"Applied profile: {profile_key}")

    # ==========================================================================
    # EVENT HANDLERS
    # ==========================================================================

    def on_device_status(self, status):
        """Handle device status updates"""
        if isinstance(status, str):
            self.status_var.set(status)

    def on_connection_change(self, connected):
        """Handle connection state changes"""
        if connected:
            self.status_var.set("Connected")
        else:
            self.status_var.set("Disconnected")

    def on_color_change(self, hex_color):
        """Handle color updates"""
        self.color_preview.config(bg=hex_color)

    def on_mode_change(self):
        """Handle mode change"""
        self.device_manager.set_mode(self.mode_var.get())
        self.effects_engine.stop_all_effects()

    def on_brightness_change(self, event):
        """Handle brightness change"""
        self.device_manager.set_brightness(int(self.brightness_var.get()))

    def on_temp_change(self, event):
        """Handle temperature change"""
        self.device_manager.set_temperature(int(self.temp_var.get()))

    def choose_color(self):
        """Open color chooser"""
        color = colorchooser.askcolor(title="Choose Lamp Color")
        if color and color[1]:
            self.effects_engine.set_color_from_hex(color[1], self.color_bright_var.get() / 1000.0)

    def toggle_rainbow(self):
        """Toggle rainbow effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return

        if self.effects_engine.rainbow_running:
            self.effects_engine.stop_rainbow_effect()
            self.rainbow_btn.config(text="Start Rainbow")
        else:
            self.effects_engine.set_rainbow_parameters(
                speed=self.rainbow_speed_var.get(),
                h_min=self.rainbow_h_min.get(),
                h_max=self.rainbow_h_max.get()
            )
            self.effects_engine.start_rainbow_effect()
            self.rainbow_btn.config(text="Stop Rainbow")

    def toggle_audio_sync(self):
        """Toggle audio sync"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected!")
            return

        if self.audio_processor.mic_running:
            self.audio_processor.stop_listening()
            self.effects_engine.stop_audio_effect()
            self.mic_btn.config(text="Start Music Sync")
        else:
            if self.audio_processor.start_listening():
                self.effects_engine.start_audio_effect()
                self.mic_btn.config(text="Stop Music Sync")

    def open_color_map_window(self):
        """Open the color map window"""
        if not COLOR_MAP_AVAILABLE:
            messagebox.showerror(
                "Not Available",
                "Color map requires: mss, pillow, numpy\n"
                "Install with: pip install mss pillow numpy"
            )
            return

        if self.color_map_window is None or not self.color_map_window.window.winfo_exists():
            self.color_map_window = ColorMapWindow(
                self.root, self.device_manager, self.effects_engine
            )

    def start_smart_ambient(self):
        """Start smart ambient lighting"""
        if not COLOR_MAP_AVAILABLE:
            messagebox.showerror("Not Available", "Install: mss, pillow, numpy")
            return

        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected!")
            return

        # Create smart ambient processor if needed
        if not hasattr(self, 'smart_ambient'):
            self.smart_ambient = SmartAmbientProcessor()

        def on_color(color):
            self.root.after(0, lambda: self.effects_engine.set_color_from_hex(color, 1.0))

        self.effects_engine.stop_all_effects()
        self.smart_ambient.start(
            color_callback=on_color,
            status_callback=lambda s: self.status_var.set(s)
        )
        self.status_var.set("Smart ambient active")

    def stop_smart_ambient(self):
        """Stop smart ambient lighting"""
        if hasattr(self, 'smart_ambient') and self.smart_ambient.is_running():
            self.smart_ambient.stop()
            self.status_var.set("Ambient stopped")

    def on_close(self):
        """Handle application close"""
        self.logger.info("Closing application...")

        # Stop smart ambient
        if hasattr(self, 'smart_ambient'):
            self.smart_ambient.stop()

        # Stop all effects
        self.effects_engine.cleanup()

        # Stop audio processing
        self.audio_processor.cleanup()

        # Close device connection
        self.device_manager.close()

        # Save configuration
        self.config.save()

        # Destroy window
        self.root.destroy()

        self.logger.info("Application closed")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    root = tk.Tk()
    app = LampControllerUI(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_close()
    except Exception as e:
        logging.getLogger(__name__).error(f"Unexpected error: {e}")
        app.on_close()


if __name__ == "__main__":
    main()
