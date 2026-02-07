#!/usr/bin/env python3
"""
Smart Lamp Controller - Improved Version
Modular architecture with better separation of concerns
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import threading
import logging
import colorsys
import time
import sys
import os
from typing import Optional

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

# Import modular components
from utils.config import Config
from core.device_manager import DeviceManager
from core.audio_processor import AudioProcessor, AUDIO_AVAILABLE
from core.ambilight_processor import AMBILIGHT_AVAILABLE
from core.effects_engine import EffectsEngine
from utils.logger_config import setup_logging, get_logger
from src.api_server import start_api_server

class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame using Canvas and Scrollbar.
    """
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create the scrollable frame inside the canvas
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure the scrollable frame to update the scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        # Add the frame to the canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure canvas resizing
        self.canvas.bind(
            "<Configure>",
            self._on_canvas_configure
        )
        
        # Configure scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack everything
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel
        self.bind_mouse_wheel(self.canvas)
        self.bind_mouse_wheel(self.scrollable_frame)

    def _on_canvas_configure(self, event):
        """Update the width of the inner frame to match the canvas"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def bind_mouse_wheel(self, widget):
        """Recursively bind mouse wheel events"""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        widget.bind("<Button-4>", self._on_mouse_wheel)    # Linux
        widget.bind("<Button-5>", self._on_mouse_wheel)    # Linux
        
        for child in widget.winfo_children():
            self.bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

class LampControllerUI:
    """Main UI class for the Smart Lamp Controller"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.logger = get_logger(__name__)
        
        # Initialize configuration
        self.config = Config()
        
        # Setup logging
        setup_logging(
            log_level="INFO",
            log_file="logs/lamp_controller.log"
        )
        
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
        
        # Setup UI
        self.setup_ui()
        self.setup_callbacks()
        
        # Start connection
        self.connect_to_device()
        
        # Start LAN REST API (no music sync) for Android/remote control
        try:
            self.api_httpd, self.api_thread = start_api_server(self.device_manager, self.effects_engine)
            self.logger.info("LAN API started on 0.0.0.0:8765")
        except Exception as e:
            self.logger.error(f"Failed to start LAN API: {e}")
        
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
        
        # Power controls
        self.setup_power_controls(main_frame)
        
        # Live Preview
        self.setup_live_preview(main_frame)
        
        # Mode selection
        self.setup_mode_selection(main_frame)
        
        # Tabbed interface
        self.setup_tabs(main_frame)
        
        self.logger.info("UI setup completed")
    
    def setup_status_bar(self, parent):
        """Setup status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            status_frame, 
            text="Status:", 
            font=("Arial", 9, "bold")
        ).pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Initializing...")
        ttk.Label(
            status_frame, 
            textvariable=self.status_var, 
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(5, 10))

        # Connection tools
        ttk.Button(status_frame, text="Check Connection", command=self.on_check_connection).pack(side=tk.RIGHT)
        ttk.Button(status_frame, text="Reconnect", command=self.on_reconnect).pack(side=tk.RIGHT, padx=(0, 6))
    
    def setup_power_controls(self, parent):
        """Setup power control buttons"""
        power_frame = ttk.LabelFrame(parent, text="Power Control", padding="10")
        power_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(power_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(
            btn_frame, 
            text="Turn ON 💡", 
            command=self.on_turn_on
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        ttk.Button(
            btn_frame, 
            text="Turn OFF 🌑", 
            command=self.on_turn_off
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # Force Reconnect
        ttk.Button(
            power_frame, 
            text="Force Reconnect 🔄", 
            command=self.on_reconnect
        ).pack(fill=tk.X, pady=(10, 0))

    def setup_live_preview(self, parent):
        """Setup live lamp preview simulation"""
        preview_frame = ttk.LabelFrame(parent, text="Live Simulation", padding="10")
        preview_frame.pack(fill=tk.X, pady=5)
        
        # Create a canvas to draw the lamp bulb
        self.preview_canvas = tk.Canvas(
            preview_frame, 
            width=60, 
            height=60, 
            bg="#f0f0f0", 
            highlightthickness=0
        )
        self.preview_canvas.pack(side=tk.LEFT, padx=20)
        
        # Draw the bulb (circle)
        self.bulb_id = self.preview_canvas.create_oval(5, 5, 55, 55, fill="#000000", outline="#666666", width=2)
        
        # Info labels
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(info_frame, text="Current Output Color").pack(anchor=tk.W)
        self.hex_label_var = tk.StringVar(value="#000000")
        ttk.Label(info_frame, textvariable=self.hex_label_var, font=("Consolas", 10)).pack(anchor=tk.W)
        
        # Performance info
        self.perf_var = tk.StringVar(value="Cmd/s: -- | Queue: --")
        ttk.Label(info_frame, textvariable=self.perf_var, font=("Consolas", 8)).pack(anchor=tk.W, pady=(5, 0))
        
        # Stats tracking
        self._fps_counts = []
        self._last_ui_fps_time = time.monotonic()
        self.root.after(1000, self.update_ui_performance_stats) # Start stats loop

        # Timeline Graph
        graph_frame = ttk.Frame(preview_frame)
        graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(20, 0))
        
        ttk.Label(graph_frame, text="Color History (Last 5s)").pack(anchor=tk.W)
        self.timeline_canvas = tk.Canvas(
            graph_frame,
            height=60,
            bg="#f0f0f0",
            highlightthickness=1,
            highlightbackground="#cccccc"
        )
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize history list
        self.color_history = []  # List of (time, hex_color)
    
    def setup_mode_selection(self, parent):
        """Setup light mode selection"""
        mode_frame = ttk.LabelFrame(parent, text="Light Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="white")
        mode_btn_frame = ttk.Frame(mode_frame)
        mode_btn_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(
            mode_btn_frame, 
            text="White Light", 
            variable=self.mode_var, 
            value="white", 
            command=self.on_mode_change
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            mode_btn_frame, 
            text="Color Light", 
            variable=self.mode_var, 
            value="colour", 
            command=self.on_mode_change
        ).pack(side=tk.LEFT, padx=10)
    
    def setup_tabs(self, parent):
        """Setup tabbed interface"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.setup_white_tab()
        self.setup_color_tab()
        self.setup_color_map_button_tab()
        self.setup_effects_tab()
        
        if AMBILIGHT_AVAILABLE:
            self.setup_ambilight_tab()
        
        if AUDIO_AVAILABLE:
            self.setup_audio_tab()
    
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
        
        self.brightness_var = tk.DoubleVar(
            value=self.config.get('effects.default_brightness', 500)
        )
        self.bright_slider = ttk.Scale(
            bright_frame, 
            from_=10, 
            to=1000, 
            variable=self.brightness_var, 
            orient=tk.HORIZONTAL
        )
        self.bright_slider.pack(fill=tk.X, pady=(5, 0))
        self.bright_slider.bind("<ButtonRelease-1>", self.on_brightness_change)
        
        # Temperature control
        temp_frame = ttk.LabelFrame(content, text="Color Temperature", padding="10")
        temp_frame.pack(fill=tk.X)
        
        ttk.Label(temp_frame, text="Temperature (Warm ← → Cool)").pack(anchor=tk.W)
        
        self.temp_var = tk.DoubleVar(
            value=self.config.get('effects.default_temperature', 500)
        )
        self.temp_slider = ttk.Scale(
            temp_frame, 
            from_=0, 
            to=1000, 
            variable=self.temp_var, 
            orient=tk.HORIZONTAL
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
        
        ttk.Label(intensity_frame, text="Brightness Level").pack(anchor=tk.W)
        
        self.color_bright_var = tk.DoubleVar(value=1000)
        self.color_bright_slider = ttk.Scale(
            intensity_frame, 
            from_=10, 
            to=1000, 
            variable=self.color_bright_var, 
            orient=tk.HORIZONTAL
        )
        self.color_bright_slider.pack(fill=tk.X, pady=(5, 0))
        self.color_bright_slider.bind("<ButtonRelease-1>", self.on_color_brightness_change)
        
        # Color picker
        picker_frame = ttk.LabelFrame(content, text="Color Selection", padding="10")
        picker_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            picker_frame, 
            text="Choose Color 🎨", 
            command=self.choose_color
        ).pack(fill=tk.X, pady=(0, 10))
        
        self.color_preview = tk.Label(
            picker_frame, 
            text="Current Color", 
            bg="#888888", 
            height=3, 
            relief="sunken"
        )
        self.color_preview.pack(fill=tk.X)
    
    def setup_color_map_button_tab(self):
        """Setup color map launcher tab with scrolling"""
        color_map_frame = ttk.Frame(self.notebook)
        self.notebook.add(color_map_frame, text="Color Map")
        
        # Use ScrollableFrame for the tab
        scroll_wrapper = ScrollableFrame(color_map_frame)
        scroll_wrapper.pack(fill=tk.BOTH, expand=True)
        
        content = ttk.Frame(scroll_wrapper.scrollable_frame, padding="30")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Center content
        center_frame = ttk.Frame(content)
        center_frame.pack(expand=True)
        
        # Icon and title
        title_frame = ttk.Frame(center_frame)
        title_frame.pack(pady=(0, 20))
        
        ttk.Label(
            title_frame,
            text="🎨",
            font=("Segoe UI", 48)
        ).pack()
        
        ttk.Label(
            title_frame,
            text="Color Map & Prevalence Analysis",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(10, 0))
        
        ttk.Label(
            title_frame,
            text="Advanced color selection with screen analysis",
            font=("Segoe UI", 10),
            foreground="#666666"
        ).pack(pady=(5, 0))
        
        # Features list
        features_frame = ttk.Frame(center_frame)
        features_frame.pack(pady=(0, 30))
        
        features = [
            "🎯 Interactive HSV color selection map",
            "📊 Real-time color prevalence analysis", 
            "🖥️ Live screen capture and highlighting",
            "🎨 Dominant color extraction",
            "⚙️ Adjustable color tolerance",
            "💡 Smart ambient lighting recommendations"
        ]
        
        for feature in features:
            ttk.Label(
                features_frame,
                text=feature,
                font=("Segoe UI", 10),
                foreground="#333333"
            ).pack(anchor=tk.W, pady=2)
        
        # Launch button
        launch_btn = ttk.Button(
            center_frame,
            text="Open Color Map Window",
            command=self.open_color_map_window,
            style="Accent.TButton"
        )
        launch_btn.pack(pady=20, ipadx=20, ipady=10)
        
        # Status
        status_frame = ttk.Frame(center_frame)
        status_frame.pack()
        
        # Check dependencies
        try:
            from color_selection_logic import SCREEN_CAPTURE_AVAILABLE
            if SCREEN_CAPTURE_AVAILABLE:
                status_text = "✅ All features available"
                status_color = "green"
            else:
                status_text = "⚠️ Install mss, pillow, numpy for full functionality"
                status_color = "orange"
        except ImportError:
            status_text = "❌ Color selection module not found"
            status_color = "red"
        
        ttk.Label(
            status_frame,
            text=status_text,
            font=("Segoe UI", 9),
            foreground=status_color
        ).pack()
        
        # Bind mouse wheel to scroll wrapper
        scroll_wrapper.bind_mouse_wheel(content)
    
    def open_color_map_window(self):
        """Open the color map window"""
        try:
            from color_map_window import open_color_map_window
            open_color_map_window(self.root, self.device_manager, self.effects_engine)
        except Exception as e:
            self.logger.error(f"Failed to open color map window: {e}")
            from tkinter import messagebox
            messagebox.showerror(
                "Error", 
                f"Failed to open color map window:\n{str(e)}\n\nMake sure color_map_window.py is available."
            )
    
    def setup_color_map_tab(self):
        """Setup interactive color map tab with scrolling"""
        color_map_frame = ttk.Frame(self.notebook)
        self.notebook.add(color_map_frame, text="Color Map")
        
        # Use ScrollableFrame for the entire tab
        scroll_wrapper = ScrollableFrame(color_map_frame)
        scroll_wrapper.pack(fill=tk.BOTH, expand=True)
        
        content = ttk.Frame(scroll_wrapper.scrollable_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Description
        desc_frame = ttk.Frame(content)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            desc_frame,
            text="Interactive Color Selection with Prevalence Analysis",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor=tk.W)
        
        ttk.Label(
            desc_frame,
            text="Click on the color map to select colors and see their prevalence on your monitor",
            font=("Segoe UI", 9),
            foreground="#666666"
        ).pack(anchor=tk.W)
        
        # Main layout
        main_layout = ttk.Frame(content)
        main_layout.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Color map
        map_frame = ttk.LabelFrame(main_layout, text="Color Selection Map", padding="10")
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Color map canvas - bigger
        self.color_map_canvas = tk.Canvas(
            map_frame,
            width=350,
            height=220,
            bg="white",
            relief="sunken",
            bd=2
        )
        self.color_map_canvas.pack(fill=tk.BOTH, expand=True)
        self.color_map_canvas.bind("<Button-1>", self.on_color_map_click)
        self.color_map_canvas.bind("<B1-Motion>", self.on_color_map_drag)
        
        # Right side - Preview and controls
        right_frame = ttk.Frame(main_layout)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Monitor preview - much bigger
        preview_frame = ttk.LabelFrame(right_frame, text="Color Prevalence Preview", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.map_preview_canvas = tk.Canvas(
            preview_frame,
            width=240,
            height=180,
            bg="#1a1a1a",
            relief="sunken",
            bd=2
        )
        self.map_preview_canvas.pack()
        
        # Prevalence info
        prevalence_frame = ttk.Frame(preview_frame)
        prevalence_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.prevalence_var = tk.StringVar(value="Select a color to analyze")
        ttk.Label(
            prevalence_frame, 
            textvariable=self.prevalence_var, 
            font=("Segoe UI", 8),
            foreground="#666666"
        ).pack(anchor=tk.W)
        
        # Tolerance control
        tolerance_frame = ttk.Frame(preview_frame)
        tolerance_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(tolerance_frame, text="Tolerance:", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        
        self.tolerance_var = tk.DoubleVar(value=0.15)
        tolerance_scale = ttk.Scale(
            tolerance_frame,
            from_=0.05,
            to=0.4,
            variable=self.tolerance_var,
            orient=tk.HORIZONTAL,
            length=80,
            command=self.on_tolerance_change
        )
        tolerance_scale.pack(side=tk.LEFT, padx=(5, 0))
        
        # Monitor selection for preview
        monitor_frame = ttk.Frame(preview_frame)
        monitor_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(monitor_frame, text="Monitor:", font=("Segoe UI", 8)).pack(side=tk.LEFT)
        
        self.map_monitor_var = tk.StringVar(value="Monitor 1")
        self.map_monitor_combo = ttk.Combobox(
            monitor_frame, 
            textvariable=self.map_monitor_var, 
            state="readonly",
            width=12,
            font=("Segoe UI", 8)
        )
        self.map_monitor_combo.pack(side=tk.LEFT, padx=(5, 0))
        self.map_monitor_combo.bind("<<ComboboxSelected>>", self.on_map_monitor_change)
        
        # Populate monitor list
        self.populate_monitor_list()
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            monitor_frame,
            text="Live",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        ).pack(side=tk.RIGHT)
        
        # Start auto-refresh
        self.refresh_timer = None
        self.start_auto_refresh()
        
        # Color info
        info_frame = ttk.LabelFrame(right_frame, text="Selected Color", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.map_color_display = tk.Label(
            info_frame,
            text="",
            bg="#ff0000",
            height=2,
            relief="sunken",
            bd=1
        )
        self.map_color_display.pack(fill=tk.X, pady=(0, 5))
        
        self.map_color_info_var = tk.StringVar(value="#FF0000")
        ttk.Label(info_frame, textvariable=self.map_color_info_var, font=("Consolas", 9)).pack(anchor=tk.W)
        
        # Dominant colors section
        dominant_frame = ttk.LabelFrame(right_frame, text="Screen Accent Colors", padding="8")
        dominant_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dominant_colors_frame = ttk.Frame(dominant_frame)
        self.dominant_colors_frame.pack(fill=tk.X)
        
        # Justification
        just_frame = ttk.LabelFrame(right_frame, text="Color Analysis", padding="8")
        just_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.map_justification_var = tk.StringVar(value="Select a color to see analysis")
        justification_label = ttk.Label(
            just_frame,
            textvariable=self.map_justification_var,
            wraplength=140,
            font=("Segoe UI", 8)
        )
        justification_label.pack(fill=tk.X)
        
        # Controls
        controls_frame = ttk.Frame(content)
        controls_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Apply button
        ttk.Button(
            controls_frame,
            text="Apply Color to Lamp 💡",
            command=self.apply_map_color
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Sample screen color button
        ttk.Button(
            controls_frame,
            text="Sample Screen �",
            command=self.sample_screen_color
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Custom color button
        ttk.Button(
            controls_frame,
            text="Custom Color 🎨",
            command=self.choose_map_custom_color
        ).pack(side=tk.LEFT)
        
        # Initialize color map
        self.root.after(100, self.create_color_map)
        
        # Bind mouse wheel to scroll wrapper
        scroll_wrapper.bind_mouse_wheel(content)
    
    def populate_monitor_list(self):
        """Populate the monitor selection dropdown"""
        monitors = ["Monitor 1"]  # Default fallback
        
        try:
            from color_selection_logic import SCREEN_CAPTURE_AVAILABLE
            if SCREEN_CAPTURE_AVAILABLE:
                import mss
                with mss.mss() as sct:
                    monitor_names = []
                    for i, monitor in enumerate(sct.monitors):
                        if i == 0:  # Skip the combined monitor
                            continue
                        monitor_names.append(f"Monitor {i} ({monitor['width']}x{monitor['height']})")
                    
                    if monitor_names:
                        monitors = monitor_names
        except Exception as e:
            self.logger.warning(f"Could not enumerate monitors: {e}")
        
        self.map_monitor_combo['values'] = monitors
        if monitors:
            self.map_monitor_combo.current(0)
    
    def on_map_monitor_change(self, event=None):
        """Handle monitor selection change"""
        try:
            selected_idx = self.map_monitor_combo.current()
            self.color_logic.monitor_index = selected_idx + 1  # mss uses 1-based indexing
            self.refresh_screen_preview()
        except Exception as e:
            self.logger.warning(f"Monitor change error: {e}")
    
    def start_auto_refresh(self):
        """Start auto-refresh of screen preview"""
        if self.auto_refresh_var.get():
            self.refresh_screen_preview()
            self.refresh_timer = self.root.after(500, self.start_auto_refresh)  # Refresh every 500ms
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
            self.refresh_timer = None
        
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
    
    def refresh_screen_preview(self):
        """Refresh the screen thumbnail preview"""
        try:
            # Capture screen thumbnail
            self.color_logic.capture_screen_thumbnail()
            self.update_map_preview()
        except Exception as e:
            self.logger.warning(f"Screen preview refresh error: {e}")
    
    def cleanup_map_resources(self):
        """Cleanup color map resources"""
        if hasattr(self, 'refresh_timer') and self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
            self.refresh_timer = None
    
    def create_color_map(self):
        """Create the HSV color map"""
        width = self.color_map_canvas.winfo_width() or 350
        height = self.color_map_canvas.winfo_height() or 220
        
        # Create HSV color wheel/map
        for x in range(0, width, 2):  # Sample every 2 pixels for performance
            for y in range(0, height, 2):
                color = self.color_logic.coordinates_to_color(x, y, width, height)
                
                # Draw pixel
                self.color_map_canvas.create_rectangle(
                    x, y, x+2, y+2,
                    fill=color,
                    outline=color
                )
        
        # Add selection indicator - bigger and more visible
        center_x = width // 2
        center_y = height // 2
        
        self.map_selection_indicator = self.color_map_canvas.create_oval(
            center_x - 8, center_y - 8, center_x + 8, center_y + 8,
            outline="white",
            width=3,
            fill="",
            tags="selection_indicator"
        )
        
        # Add inner circle for better visibility
        self.map_selection_inner = self.color_map_canvas.create_oval(
            center_x - 4, center_y - 4, center_x + 4, center_y + 4,
            outline="black",
            width=2,
            fill="",
            tags="selection_indicator"
        )
        
        # Initialize preview
        self.update_map_preview()
    
    def on_color_map_click(self, event):
        """Handle click on color map"""
        self.update_map_selection_from_click(event.x, event.y)
    
    def on_color_map_drag(self, event):
        """Handle drag on color map"""
        self.update_map_selection_from_click(event.x, event.y)
    
    def update_map_selection_from_click(self, x: int, y: int):
        """Update color selection from click coordinates"""
        width = self.color_map_canvas.winfo_width() or 350
        height = self.color_map_canvas.winfo_height() or 220
        
        # Get color from coordinates
        color = self.color_logic.coordinates_to_color(x, y, width, height)
        position = (x / width, y / height)
        
        # Update logic
        self.color_logic.update_selection(color, position)
        
        # Update UI
        self.update_map_selection_indicator(x, y)
        self.update_map_color_info()
        self.update_map_preview()
    
    def update_map_selection_indicator(self, x: int, y: int):
        """Update the selection indicator position"""
        # Update outer circle
        self.color_map_canvas.coords(
            self.map_selection_indicator,
            x - 8, y - 8, x + 8, y + 8
        )
        
        # Update inner circle
        self.color_map_canvas.coords(
            self.map_selection_inner,
            x - 4, y - 4, x + 4, y + 4
        )
    
    def update_map_color_info(self):
        """Update color information display"""
        info = self.color_logic.get_selection_info()
        
        self.map_color_display.config(bg=info['color'])
        self.map_color_info_var.set(info['color'].upper())
    
    def update_map_preview(self):
        """Update the monitor preview with color prevalence analysis"""
        self.map_preview_canvas.delete("all")
        
        info = self.color_logic.get_selection_info()
        color = info['color']
        
        canvas_width = 240
        canvas_height = 180
        
        # Analyze color prevalence
        tolerance = self.tolerance_var.get()
        prevalence_data = self.color_logic.analyze_color_prevalence(color, tolerance)
        
        if prevalence_data:
            # Show highlighted image
            highlighted_tk = None
            try:
                from PIL import ImageTk
                # Resize the highlighted image to fit the bigger canvas
                highlighted_img = prevalence_data['highlighted_image']
                highlighted_img = highlighted_img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                highlighted_tk = ImageTk.PhotoImage(highlighted_img)
            except Exception:
                pass
            
            if highlighted_tk:
                self.map_preview_canvas.create_image(
                    canvas_width // 2, canvas_height // 2,
                    image=highlighted_tk,
                    tags="preview"
                )
                # Keep reference
                self.map_preview_canvas.highlighted_ref = highlighted_tk
            
            # Update prevalence info
            prevalence = prevalence_data['prevalence_percent']
            if prevalence > 15:
                status = "Excellent choice! High color presence"
                color_status = "green"
            elif prevalence > 8:
                status = "Good choice - Moderate presence"
                color_status = "orange"
            elif prevalence > 3:
                status = "Low presence - Consider other colors"
                color_status = "red"
            else:
                status = "Very low presence - Poor choice"
                color_status = "red"
            
            self.prevalence_var.set(f"{prevalence:.1f}% of screen - {status}")
            
            # Update justification with prevalence info
            base_justification = info['justification']
            prevalence_note = f" Color covers {prevalence:.1f}% of screen content."
            self.map_justification_var.set(base_justification + prevalence_note)
            
        else:
            # Fallback: show regular thumbnail or mock screen
            thumbnail_tk = self.color_logic.get_screen_thumbnail_tk()
            
            if thumbnail_tk:
                # Resize thumbnail to fit bigger canvas
                try:
                    from PIL import ImageTk
                    thumbnail_img = self.color_logic.screen_thumbnail
                    if thumbnail_img:
                        thumbnail_img = thumbnail_img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                        thumbnail_tk = ImageTk.PhotoImage(thumbnail_img)
                except Exception:
                    pass
                
                self.map_preview_canvas.create_image(
                    canvas_width // 2, canvas_height // 2,
                    image=thumbnail_tk,
                    tags="preview"
                )
                self.map_preview_canvas.thumbnail_ref = thumbnail_tk
            else:
                # Mock screen
                self.map_preview_canvas.create_rectangle(
                    5, 5, canvas_width - 5, canvas_height - 5,
                    fill="#000000",
                    outline="#666666",
                    width=2,
                    tags="preview"
                )
                
                self.map_preview_canvas.create_text(
                    canvas_width // 2, canvas_height // 2,
                    text="Screen Preview\nUnavailable\n\nInstall: pip install mss pillow numpy",
                    fill="#666666",
                    font=("Segoe UI", 10),
                    justify=tk.CENTER,
                    tags="preview"
                )
            
            self.prevalence_var.set("Analysis unavailable - install numpy")
        
        # Update dominant colors
        self.update_dominant_colors()
    
    def update_dominant_colors(self):
        """Update the dominant colors display"""
        # Clear existing dominant color widgets
        for widget in self.dominant_colors_frame.winfo_children():
            widget.destroy()
        
        dominant_colors = self.color_logic.get_dominant_colors(4)
        
        if dominant_colors:
            for i, (color, percentage) in enumerate(dominant_colors):
                color_frame = ttk.Frame(self.dominant_colors_frame)
                color_frame.pack(fill=tk.X, pady=1)
                
                # Color swatch
                color_btn = tk.Button(
                    color_frame,
                    text="",
                    bg=color,
                    width=3,
                    height=1,
                    relief="raised",
                    bd=1,
                    command=lambda c=color: self.select_dominant_color(c)
                )
                color_btn.pack(side=tk.LEFT, padx=(0, 5))
                
                # Percentage label
                ttk.Label(
                    color_frame,
                    text=f"{percentage:.1f}%",
                    font=("Segoe UI", 7)
                ).pack(side=tk.LEFT)
        else:
            ttk.Label(
                self.dominant_colors_frame,
                text="No dominant colors found",
                font=("Segoe UI", 8),
                foreground="#666666"
            ).pack()
    
    def select_dominant_color(self, color: str):
        """Select a dominant color from the accent colors"""
        # Update color logic
        self.color_logic.update_selection(color, self.color_logic.selected_position)
        
        # Update UI
        self.update_map_color_info()
        self.update_map_preview()
        
        # Update selection indicator on color map
        width = self.color_map_canvas.winfo_width() or 350
        height = self.color_map_canvas.winfo_height() or 220
        x, y = self.color_logic.color_to_coordinates(color, width, height)
        self.update_map_selection_indicator(x, y)
    
    def on_tolerance_change(self, value=None):
        """Handle tolerance slider change"""
        # Update preview with new tolerance
        self.update_map_preview()
    
    def apply_map_color(self):
        """Apply the selected color from color map to the lamp"""
        if not self.device_manager.is_connected:
            self.status_var.set("Error: Not connected to lamp!")
            return
        
        info = self.color_logic.get_selection_info()
        color = info['color']
        
        try:
            # Stop any running effects first
            self.effects_engine.stop_all_effects()
            self._reset_effect_buttons()
            
            # Set color mode and apply color
            self.mode_var.set("colour")
            self.device_manager.set_mode("colour")
            self.effects_engine.set_color_from_hex(color, self.color_bright_var.get() / 1000.0)
            
            self.status_var.set(f"Applied color map selection: {color}")
            
        except Exception as e:
            self.status_var.set(f"Error applying color: {str(e)}")
    
    def choose_map_custom_color(self):
        """Open custom color chooser for color map"""
        from tkinter import colorchooser
        
        current_color = self.color_logic.selected_color
        color = colorchooser.askcolor(
            title="Choose Custom Color",
            initialcolor=current_color
        )
        
        if color and color[1]:
            # Update color logic
            self.color_logic.update_selection(color[1], self.color_logic.selected_position)
            
            # Update UI
            self.update_map_color_info()
            self.update_map_preview()
            
            # Update selection indicator to approximate position
            width = self.color_map_canvas.winfo_width() or 350
            height = self.color_map_canvas.winfo_height() or 220
            x, y = self.color_logic.color_to_coordinates(color[1], width, height)
            self.update_map_selection_indicator(x, y)
    
    def sample_screen_color(self):
        """Sample the actual color from the screen at the selected position"""
        try:
            position = self.color_logic.selected_position
            sampled_color = self.color_logic.get_color_at_screen_position(
                position, 
                self.color_logic.monitor_index
            )
            
            if sampled_color:
                # Update color logic with sampled color
                self.color_logic.update_selection(sampled_color, position)
                
                # Update UI
                self.update_map_color_info()
                self.update_map_preview()
                
                # Update selection indicator
                width = self.color_map_canvas.winfo_width() or 350
                height = self.color_map_canvas.winfo_height() or 220
                x, y = self.color_logic.color_to_coordinates(sampled_color, width, height)
                self.update_map_selection_indicator(x, y)
                
                self.status_var.set(f"Sampled screen color: {sampled_color}")
            else:
                self.status_var.set("Could not sample screen color")
                
        except Exception as e:
            self.status_var.set(f"Screen sampling error: {str(e)}")
    
    def setup_effects_tab(self):
        """Setup effects control tab"""
        effects_frame = ttk.Frame(self.notebook)
        self.notebook.add(effects_frame, text="Effects")
        
        # Use ScrollableFrame for effects tab
        scroll_wrapper = ScrollableFrame(effects_frame)
        scroll_wrapper.pack(fill=tk.BOTH, expand=True)
        
        content = ttk.Frame(scroll_wrapper.scrollable_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Rainbow effect
        rainbow_frame = ttk.LabelFrame(content, text="Rainbow Effect", padding="10")
        rainbow_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Rainbow preview
        preview_frame = ttk.Frame(rainbow_frame)
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(preview_frame, text="Rainbow Preview:").pack(anchor=tk.W)
        self.rainbow_canvas = tk.Canvas(
            preview_frame, 
            height=40, 
            bg="white", 
            relief="sunken", 
            bd=2
        )
        self.rainbow_canvas.pack(fill=tk.X, pady=(5, 0))
        
        # Speed control
        ttk.Label(rainbow_frame, text="Animation Speed").pack(anchor=tk.W)
        
        self.rainbow_speed_var = tk.DoubleVar(
            value=self.config.get('effects.rainbow_speed', 50)
        )
        ttk.Scale(
            rainbow_frame, 
            from_=1, 
            to=100, 
            variable=self.rainbow_speed_var, 
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_rainbow_preview()
        ).pack(fill=tk.X, pady=(5, 10))
        
        # Hue range controls
        range_frame = ttk.Frame(rainbow_frame)
        range_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(range_frame, text="Color Range - Start Hue").pack(anchor=tk.W)
        self.rainbow_h_min = tk.DoubleVar(value=0.0)
        self.hue_min_scale = ttk.Scale(
            range_frame, 
            from_=0.0, 
            to=1.0, 
            variable=self.rainbow_h_min, 
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_rainbow_preview()
        )
        self.hue_min_scale.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(range_frame, text="Color Range - End Hue").pack(anchor=tk.W)
        self.rainbow_h_max = tk.DoubleVar(value=1.0)
        self.hue_max_scale = ttk.Scale(
            range_frame, 
            from_=0.0, 
            to=1.0, 
            variable=self.rainbow_h_max, 
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_rainbow_preview()
        )
        self.hue_max_scale.pack(fill=tk.X)
        
        # Rainbow control button
        self.rainbow_btn = ttk.Button(
            rainbow_frame, 
            text="Start Rainbow 🌈", 
            command=self.toggle_rainbow
        )
        self.rainbow_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Initialize rainbow preview
        self.update_rainbow_preview()
        
        # Blinker effect
        blinker_frame = ttk.LabelFrame(content, text="Blinker / Party Mode", padding="10")
        blinker_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(blinker_frame, text="Blink Speed").pack(anchor=tk.W)
        self.blinker_speed_var = tk.DoubleVar(value=50)
        ttk.Scale(
            blinker_frame,
            from_=1,
            to=100,
            variable=self.blinker_speed_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_blinker_parameters()
        ).pack(fill=tk.X, pady=(5, 10))

        self.blinker_btn = ttk.Button(
            blinker_frame,
            text="Start Blinker 🎉",
            command=self.toggle_blinker
        )
        self.blinker_btn.pack(fill=tk.X)

        # Strobe effect
        strobe_frame = ttk.LabelFrame(content, text="Strobe / Party On-Off", padding="10")
        strobe_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(strobe_frame, text="Strobe Speed").pack(anchor=tk.W)
        self.strobe_speed_var = tk.DoubleVar(value=80)
        ttk.Scale(
            strobe_frame,
            from_=1,
            to=100,
            variable=self.strobe_speed_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_strobe_parameters()
        ).pack(fill=tk.X, pady=(5, 10))

        self.strobe_btn = ttk.Button(
            strobe_frame,
            text="Start Strobe ⚡",
            command=self.toggle_strobe
        )
        self.strobe_btn.pack(fill=tk.X)

        # White Strobe effect
        white_strobe_frame = ttk.LabelFrame(content, text="White Strobe / Party Flash", padding="10")
        white_strobe_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(white_strobe_frame, text="Flash Speed").pack(anchor=tk.W)
        self.white_strobe_speed_var = tk.DoubleVar(value=80)
        ttk.Scale(
            white_strobe_frame,
            from_=1,
            to=100,
            variable=self.white_strobe_speed_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_white_strobe_parameters()
        ).pack(fill=tk.X, pady=(5, 10))

        self.white_strobe_btn = ttk.Button(
            white_strobe_frame,
            text="Start White Strobe ⚡",
            command=self.toggle_white_strobe
        )
        self.white_strobe_btn.pack(fill=tk.X)
        
        # Built-in Scenes
        scenes_frame = ttk.LabelFrame(content, text="Built-in Scenes (Tuya)", padding="10")
        scenes_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(scenes_frame, text="Select a hardware scene:", font=("Segoe UI", 8, "italic")).pack(anchor=tk.W, pady=(0, 10))
        
        # Some common scene strings found in Tuya devices
        # Note: These are specific to certain firmware versions but often work across brands
        tuya_scenes = [
            ("Night", "000e0d00002e03e802cc00000000"),
            ("Read", "010e0d00002e03e802cc00000000"),
            ("Working", "020e0d00002e03e802cc00000000"),
            ("Leisure", "030e0d00002e03e802cc00000000"),
            ("Soft", "04464602007803e803e800000000464602007803e803e800000000"),
            ("Colorful", "05464601000003e803e800000000464601007803e803e80000000046460100f003e803e800000000"),
            ("Dazzling", "06464601000003e803e800000000464601007803e803e80000000046460100f003e803e800000000"),
            ("Gorgeous", "07464602000003e803e800000000464602007803e803e80000000046460200f003e803e800000000"),
        ]
        
        btn_grid = ttk.Frame(scenes_frame)
        btn_grid.pack(fill=tk.X)
        
        for i, (name, data) in enumerate(tuya_scenes):
            row, col = divmod(i, 2)
            btn = ttk.Button(
                btn_grid, 
                text=name, 
                command=lambda d=data: self.on_set_scene(d)
            )
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            btn_grid.columnconfigure(col, weight=1)
            
        # Bind mouse wheel to all children
        scroll_wrapper.bind_mouse_wheel(content)
    
    def setup_audio_tab(self):
        """Setup audio synchronization tab"""
        if not AUDIO_AVAILABLE:
            return
        
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="Music Sync")
        
        # Use ScrollableFrame for audio tab
        scroll_wrapper = ScrollableFrame(audio_frame)
        scroll_wrapper.pack(fill=tk.BOTH, expand=True)
        
        content = ttk.Frame(scroll_wrapper.scrollable_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Audio mode selection
        mode_frame = ttk.LabelFrame(content, text="Audio Reactive Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.audio_mode = tk.StringVar(value="rms_both")
        
        modes = [
            ("rms_both", "RMS: Volume → Brightness + Color"),
            ("rms_brightness", "RMS: Volume → Brightness Only"),
            ("beat_color", "Beat Detection → Color Changes"),
            ("beat_white_flash", "Beat Detection → White Flash ⚡"),
            ("frequency_bands", "Frequency Bands → Rainbow")
        ]
        
        for value, text in modes:
            ttk.Radiobutton(
                mode_frame, 
                text=text, 
                variable=self.audio_mode, 
                value=value
            ).pack(anchor=tk.W, pady=2)
        
        # Beat sensitivity
        sens_frame = ttk.Frame(mode_frame)
        sens_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(sens_frame, text="Beat Sensitivity:").pack(side=tk.LEFT)
        
        self.beat_sensitivity = tk.DoubleVar(
            value=self.config.get('audio.default_sensitivity', 2.5)
        )
        ttk.Scale(
            sens_frame, 
            from_=0.5, 
            to=8.0, 
            variable=self.beat_sensitivity, 
            orient=tk.HORIZONTAL, 
            length=200
        ).pack(side=tk.LEFT, padx=(10, 0))
        # Apply sensitivity changes live while music mode is running
        try:
            self.beat_sensitivity.trace_add("write", lambda *_: self.on_sensitivity_change())
            self.viz_gain_var.trace_add("write", lambda *_: self.update_audio_visualization(getattr(self.audio_processor, 'audio_levels', [])))
            self.viz_bars_var.trace_add("write", lambda *_: self.update_audio_visualization(getattr(self.audio_processor, 'audio_levels', [])))
            self.viz_mode_var.trace_add("write", lambda *_: self.update_audio_visualization(getattr(self.audio_processor, 'audio_levels', [])))
        except Exception:
            pass
        
        # BPM display
        self.bpm_label = ttk.Label(
            mode_frame, 
            text="BPM: --", 
            font=("Arial", 10, "bold")
        )
        self.bpm_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Audio visualization
        viz_frame = ttk.LabelFrame(content, text="Audio Level Visualization", padding="10")
        viz_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.audio_canvas = tk.Canvas(
            viz_frame, 
            height=80, 
            bg="black", 
            relief="sunken", 
            bd=2
        )
        self.audio_canvas.pack(fill=tk.X)

        # Visualization controls
        viz_ctrl = ttk.Frame(viz_frame)
        viz_ctrl.pack(fill=tk.X, pady=(8, 0))

        # Viz mode
        ttk.Label(viz_ctrl, text="Viz:").grid(row=0, column=0, sticky=tk.W)
        self.viz_mode_var = tk.StringVar(value="levels")
        ttk.Radiobutton(viz_ctrl, text="Levels", variable=self.viz_mode_var, value="levels").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(viz_ctrl, text="Reactive Spectrum", variable=self.viz_mode_var, value="spectrum").grid(row=0, column=2, padx=(6, 12), sticky=tk.W)

        # Viz Gain
        ttk.Label(viz_ctrl, text="Viz Gain:").grid(row=1, column=0, sticky=tk.W)
        self.viz_gain_var = tk.DoubleVar(value=2.0)
        ttk.Scale(viz_ctrl, from_=0.5, to=4.0, variable=self.viz_gain_var,
                  orient=tk.HORIZONTAL, length=180).grid(row=1, column=1, padx=(6, 12), sticky=tk.W)

        # Bars count
        ttk.Label(viz_ctrl, text="Bars:").grid(row=1, column=2, sticky=tk.W)
        self.viz_bars_var = tk.IntVar(value=40)
        ttk.Scale(viz_ctrl, from_=10, to=80, variable=self.viz_bars_var,
                  orient=tk.HORIZONTAL, length=180).grid(row=1, column=3, padx=(6, 0), sticky=tk.W)

        # Sensitivity label indicator
        self.sens_label_var = tk.StringVar(value="Medium")
        ttk.Label(viz_frame, textvariable=self.sens_label_var).pack(anchor=tk.W, pady=(6, 0))
        
        # Device selection
        device_frame = ttk.LabelFrame(content, text="Audio Input Device", padding="10")
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(device_frame, text="Select Input Device:").pack(anchor=tk.W, pady=(0, 5))
        
        if self.audio_processor.audio_devices:
            dev_names = [d[1] for d in self.audio_processor.audio_devices]
            dev_ids = [d[0] for d in self.audio_processor.audio_devices]
            
            self.device_combo = ttk.Combobox(device_frame, values=dev_names, state="readonly")
            self.device_combo.pack(fill=tk.X, pady=(0, 5))
            
            # Set default device
            default_idx = self.audio_processor.get_default_input_device_index()
            try:
                list_pos = next((i for i, v in enumerate(dev_ids) if v == default_idx), 0)
                self.device_combo.current(list_pos)
            except:
                self.device_combo.current(0)
            
            self.device_combo.bind("<<ComboboxSelected>>", self.on_audio_device_change)
            
        # Bind mouse wheel to all children
        scroll_wrapper.bind_mouse_wheel(content)
        
        # Complete setup
        self._setup_audio_service_controls(scroll_wrapper, content, device_frame)

    def setup_ambilight_tab(self):
        """Setup screen synchronization (Ambilight) tab"""
        ambi_frame = ttk.Frame(self.notebook)
        self.notebook.add(ambi_frame, text="Screen Sync")
        
        # Use ScrollableFrame for the sync tab
        scroll_frame = ScrollableFrame(ambi_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        content = scroll_frame.scrollable_frame
        
        # Add mouse wheel binding to the canvas for scrolling
        def _on_mousewheel(event):
            scroll_frame.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        scroll_frame.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Header
        ttk.Label(content, text="Ambilight / Screen Sync", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))
        ttk.Label(content, text="Synchronizes the lamp with your main monitor's dominant color.", wraplength=400).pack(pady=(0, 20))
        
        # Controls Frame
        ctrl_frame = ttk.LabelFrame(content, text="Settings", padding="15")
        ctrl_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Alpha/Smoothing
        ttk.Label(ctrl_frame, text="Smoothing (Response speed):").pack(anchor=tk.W)
        self.ambi_alpha_var = tk.DoubleVar(value=0.2)
        alpha_scale = ttk.Scale(
            ctrl_frame, 
            from_=0.05, 
            to=0.6, 
            variable=self.ambi_alpha_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.on_ambilight_smoothing_change()
        )
        alpha_scale.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(ctrl_frame, text="Slow / Smooth <───────────────────> Fast / Reactive", font=("Segoe UI", 7, "italic")).pack(fill=tk.X, pady=(0, 15))

        # Edge Cropping
        ttk.Label(ctrl_frame, text="Edge Crop % (Ignore Taskbar/Headers):").pack(anchor=tk.W)
        self.ambi_crop_var = tk.IntVar(value=15)
        crop_scale = ttk.Scale(
            ctrl_frame,
            from_=0,
            to=35,
            variable=self.ambi_crop_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.on_ambilight_crop_change()
        )
        crop_scale.pack(fill=tk.X, pady=(5, 5))
        ttk.Label(ctrl_frame, text="Full Screen <───────────────────────> Center Only", font=("Segoe UI", 7, "italic")).pack(fill=tk.X, pady=(0, 15))

        # Monitor selection
        ttk.Label(ctrl_frame, text="Select Display:").pack(anchor=tk.W)
        self.ambi_monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(ctrl_frame, textvariable=self.ambi_monitor_var, state="readonly")
        
        monitors = []
        if AMBILIGHT_AVAILABLE:
            try:
                import mss
                from screeninfo import get_monitors
                
                # Get descriptive names from screeninfo
                screen_names = {}
                try:
                    for m in get_monitors():
                        # Key by geometry to match with mss
                        key = (m.x, m.y, m.width, m.height)
                        screen_names[key] = f"{m.name} {'(Primary)' if m.is_primary else ''}".strip()
                except Exception:
                    pass

                with mss.mss() as sct:
                    for i, m in enumerate(sct.monitors):
                        if i == 0: continue # Skip 'all monitors' virtual display
                        
                        key = (m['left'], m['top'], m['width'], m['height'])
                        name = screen_names.get(key, f"Display {i}")
                        monitors.append(f"{name} ({m['width']}x{m['height']})")
            except Exception:
                # Basic fallback
                try:
                    import mss
                    with mss.mss() as sct:
                        for i, m in enumerate(sct.monitors):
                            if i == 0: continue
                            monitors.append(f"Display {i} ({m['width']}x{m['height']})")
                except Exception:
                    pass
        
        if not monitors:
            monitors = ["Primary Display"]
            
        self.monitor_combo['values'] = monitors
        self.monitor_combo.current(0)
        self.monitor_combo.pack(fill=tk.X, pady=(5, 10))
        self.monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.on_ambilight_monitor_change())

        # Start/Stop Button (Screen Sync only)
        self.ambi_btn = ttk.Button(
            content, 
            text="Start Screen Sync 🖥️", 
            command=self.toggle_ambilight
        )
        self.ambi_btn.pack(fill=tk.X, ipady=10)
        # Minimal screen sync tab: removed old extra info/controls
        ttk.Separator(content, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # Test Screen section (for verifying lamp response visually)
        test_frame = ttk.LabelFrame(content, text="Test Screen", padding=10)
        test_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(test_frame, text="Open a test window with color bars and patches.").pack(anchor=tk.W)
        ttk.Button(test_frame, text="Open Test Pattern ▶", command=self.open_test_pattern).pack(fill=tk.X, pady=(6, 0))
        
        # Smart Ambient Section
        ttk.Label(content, text="Smart Ambient Lighting", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))
        ttk.Label(content, text="Automatically selects the best accent colors from your screen for ambient lighting.", wraplength=400).pack(pady=(0, 20))
        
        # Smart Ambient Controls
        smart_ctrl_frame = ttk.LabelFrame(content, text="Smart Ambient Settings", padding="15")
        smart_ctrl_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Update interval
        ttk.Label(smart_ctrl_frame, text="Update Interval (seconds):").pack(anchor=tk.W)
        self.smart_interval_var = tk.DoubleVar(value=1.0)
        interval_scale = ttk.Scale(
            smart_ctrl_frame, 
            from_=0.5, 
            to=5.0, 
            variable=self.smart_interval_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.on_smart_interval_change()
        )
        interval_scale.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(smart_ctrl_frame, text="Fast (0.5s) <───────────────────> Slow (5s)", font=("Segoe UI", 7, "italic")).pack(fill=tk.X, pady=(0, 15))
        
        # Monitor selection for smart ambient
        ttk.Label(smart_ctrl_frame, text="Monitor for Analysis:").pack(anchor=tk.W)
        self.smart_monitor_var = tk.StringVar()
        self.smart_monitor_combo = ttk.Combobox(smart_ctrl_frame, textvariable=self.smart_monitor_var, state="readonly")
        self.smart_monitor_combo['values'] = monitors  # Use same monitor list
        self.smart_monitor_combo.current(0)
        self.smart_monitor_combo.pack(fill=tk.X, pady=(5, 10))
        self.smart_monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.on_smart_monitor_change())
        
        # Status display
        self.smart_status_var = tk.StringVar(value="Smart ambient lighting stopped")
        ttk.Label(smart_ctrl_frame, textvariable=self.smart_status_var, font=("Segoe UI", 9), foreground="#666666").pack(anchor=tk.W, pady=(10, 0))
        
        # Start/Stop Button for Smart Ambient
        self.smart_ambi_btn = ttk.Button(
            content, 
            text="Start Smart Ambient 🎯", 
            command=self.toggle_smart_ambient
        )
        self.smart_ambi_btn.pack(fill=tk.X, ipady=10)
        
        # Tech details
        tech_frame = ttk.Frame(content)
        tech_frame.pack(fill=tk.X, pady=(30, 0))
        ttk.Label(tech_frame, text="Tech: HSV-Weighted dominant color extraction with temporal smoothing.", font=("Segoe UI", 8, "italic"), foreground="gray").pack()
        ttk.Label(tech_frame, text="Smart Ambient: Intelligent color scoring with grayscale filtering.", font=("Segoe UI", 8, "italic"), foreground="gray").pack()

    def _setup_audio_service_controls(self, scroll_wrapper, content, device_frame):
        # Helper to finish audio tab setup (fixing indentation mess)
        if self.audio_processor.audio_devices:
            # Restart control
            ttk.Button(device_frame, text="Restart Audio Service", command=self.restart_audio_service).pack(fill=tk.X)
        else:
            ttk.Label(device_frame, text="No audio devices found").pack()
        
        # Music sync control
        sync_frame = ttk.LabelFrame(content, text="Music Synchronization", padding="10")
        sync_frame.pack(fill=tk.X)
        
        ttk.Label(sync_frame, text="Choose how the lamp reacts to audio input").pack(pady=(0, 10))
        

        self.mic_btn = ttk.Button(
            sync_frame, 
            text="Start Music Sync 🎤", 
            command=self.toggle_audio_sync
        )
        self.mic_btn.pack(fill=tk.X)
        
        # Bind mouse wheel to all children
        scroll_wrapper.bind_mouse_wheel(content)
    
    def setup_callbacks(self):
        """Setup callbacks between components"""
        # Device manager callbacks
        self.device_manager.add_status_callback(self.on_device_status)
        self.device_manager.add_connection_callback(self.on_connection_change)
        
        # Effects engine callbacks
        self.effects_engine.add_color_callback(self.on_color_change)
        self.effects_engine.add_status_callback(self.on_effect_status)
        
        # Audio processor callbacks
        if AUDIO_AVAILABLE:
            self.audio_processor.add_level_callback(self.update_audio_visualization)
            self.audio_processor.add_bpm_callback(self.update_bpm_display)
    
    def connect_to_device(self):
        """Connect to the lamp device"""
        def connect_thread():
            success = self.device_manager.connect()
            if success:
                self.logger.info("Successfully connected to device")
            else:
                self.logger.error("Failed to connect to device")
        
        threading.Thread(target=connect_thread, daemon=True).start()

    def on_check_connection(self):
        """Check current connection in a background thread"""
        def _check():
            self.device_manager.check_connection()
        threading.Thread(target=_check, daemon=True).start()

    def on_reconnect(self):
        """Reconnect to device in a background thread"""
        def _reconn():
            self.status_var.set("Reconnecting...")
            ok = self.device_manager.reconnect()
            if ok:
                self.logger.info("Reconnected to device")
            else:
                self.logger.error("Reconnect failed")
        threading.Thread(target=_reconn, daemon=True).start()
    
    # Event handlers
    def on_device_status(self, status):
        """Handle device status updates"""
        self.root.after(0, self._on_device_status_main_thread, status)

    def _on_device_status_main_thread(self, status):
        """Main thread handler for device status"""
        if isinstance(status, str):
            self.status_var.set(status)
        elif isinstance(status, dict):
            # Update UI variables from device status
            if 'mode' in status:
                self.mode_var.set(status['mode'])
            if 'brightness' in status:
                self.brightness_var.set(status['brightness'])
            if 'temperature' in status:
                self.temp_var.set(status['temperature'])
    
    def on_connection_change(self, connected):
        """Handle connection state changes"""
        self.root.after(0, self._on_connection_change_main_thread, connected)

    def _on_connection_change_main_thread(self, connected):
        if connected:
            self.logger.info("Device connected")
        else:
            self.logger.warning("Device disconnected")
    
    
    def on_color_change(self, hex_color):
        """Handle color change updates (Called from background threads)"""
        # PERF: Throttle at the source of the callback to avoid flooding the main thread queue
        now = time.monotonic()
        if not hasattr(self, '_last_color_callback_time'):
            self._last_color_callback_time = 0
            
        # Limit to ~60 updates/sec to main thread
        if now - self._last_color_callback_time < 0.016:
            return
        self._last_color_callback_time = now
        
        self.root.after(0, self._on_color_change_main_thread, hex_color)

    def _on_color_change_main_thread(self, hex_color):
        """Handle color change updates on the main UI thread"""
        if hasattr(self, 'color_preview'):
            self.color_preview.config(bg=hex_color)
        
        if hasattr(self, 'preview_canvas') and hasattr(self, 'bulb_id'):
            self.preview_canvas.itemconfig(self.bulb_id, fill=hex_color)
            # Add a "glow" effect by changing outline or just keeping it simple
            if hex_color.lower() == "#000000":
                self.preview_canvas.itemconfig(self.bulb_id, outline="#444444")
            else:
                self.preview_canvas.itemconfig(self.bulb_id, outline=hex_color)
        
        if hasattr(self, 'hex_label_var'):
            self.hex_label_var.set(hex_color)

        # Update Timeline
        if hasattr(self, 'timeline_canvas'):
            current_time = time.monotonic()
            self.color_history.append((current_time, hex_color))
            
            # Prune old history (keep last 5 seconds)
            cutoff = current_time - 5.0
            self.color_history = [x for x in self.color_history if x[0] > cutoff]
            
            # but for smoothness we draw immediately here as it's simple lines
            # PERF: Only redraw if enough time has passed (e.g., 30 FPS cap)
            if not hasattr(self, '_last_timeline_draw'):
                self._last_timeline_draw = 0
            
            # FPS Tracking
            self._fps_counts.append(current_time)
            self._fps_counts = [t for t in self._fps_counts if current_time - t < 1.0]

            if current_time - self._last_timeline_draw > 0.05:  # Throttled to 20 FPS for timeline
                self.draw_timeline_graph(current_time)
                self._last_timeline_draw = current_time

    def update_ui_performance_stats(self):
        """Update performance statistics label periodically"""
        now = time.monotonic()
        
        # Calculate commands per second (target) - already pruned to 1s window in callback
        cmd_rate = len(self._fps_counts)
        
        # Get queue size from device manager
        q_size = self.device_manager.get_queue_size()
            
        # Update label
        self.perf_var.set(f"Cmd Target: {cmd_rate}/s | Queue: {q_size}")
        
        # Schedule next update
        self._last_ui_fps_time = now
        self.root.after(500, self.update_ui_performance_stats)

    def draw_timeline_graph(self, current_time):
        """Draw history graph on canvas (Optimized)"""
        if not self.color_history:
            return
            
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        
        # Don't draw if window too small
        if width < 10:
            return

        self.timeline_canvas.delete("all")
        
        # Map 5 seconds to width
        time_span = 5.0
        
        if len(self.color_history) < 1:
            return

        # Simple algorithm to combine adjacent segments of the same color
        combined_segments = []
        if self.color_history:
            start_t, color = self.color_history[0]
            for i in range(1, len(self.color_history)):
                t, c = self.color_history[i]
                if c != color:
                    combined_segments.append((start_t, t, color))
                    start_t, color = t, c
            combined_segments.append((start_t, current_time, color))

        # Draw combined segments
        for t1, t2, color in combined_segments:
            age1 = current_time - t1
            age2 = current_time - t2
            
            x1 = width - (age1 / time_span) * width
            x2 = width - (age2 / time_span) * width
            
            x1 = max(0, x1)
            x2 = min(width, x2)
            
            if x2 > x1:
                # Use a small outline overlap or no outline to avoid gaps
                self.timeline_canvas.create_rectangle(x1, 0, x2 + 1, height, fill=color, outline="")
    
    def on_effect_status(self, status):
        """Handle effect status updates"""
        self.root.after(0, self._on_effect_status_main_thread, status)

    def _on_effect_status_main_thread(self, status):
        # Strictly sanitize to ASCII to avoid any console/file handler encoding issues (e.g., cp1252)
        try:
            safe = status.encode('ascii', errors='ignore').decode('ascii')
        except Exception:
            safe = str(status).encode('ascii', errors='ignore').decode('ascii')
        self.logger.info("Effect status: %s", safe)
        
        # Handle smart ambient status updates
        if hasattr(self, 'smart_status_var') and ("🎯" in status or "Smart ambient" in status or "Auto-applied" in status or "No suitable colors" in status or "No colors detected" in status):
            self.smart_status_var.set(status)
    
    def open_test_pattern(self):
        """Open a simple test pattern window with color bars to evaluate lamp output"""
        import tkinter as tk
        from tkinter import ttk
        try:
            if hasattr(self, '_test_pattern_win') and self._test_pattern_win and tk.Toplevel.winfo_exists(self._test_pattern_win):
                self._test_pattern_win.lift()
                return
        except Exception:
            pass
        win = tk.Toplevel(self.root)
        self._test_pattern_win = win
        win.title("Test Pattern - Color Bars")
        win.geometry("800x450")
        win.minsize(600, 340)
        container = ttk.Frame(win, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, bg="#000000")
        canvas.pack(fill=tk.BOTH, expand=True)
        info = ttk.Label(container, text="Resize the window to scale the pattern. Use this to check lamp color following.")
        info.pack(anchor=tk.W, pady=(8,0))

        def draw_pattern():
            canvas.delete("all")
            w = max(100, canvas.winfo_width())
            h = max(100, canvas.winfo_height())
            # SMPTE-like color bars (approximate)
            bars = [
                "#ffffff",  # white
                "#ffff00",  # yellow
                "#00ffff",  # cyan
                "#00ff00",  # green
                "#ff00ff",  # magenta
                "#ff0000",  # red
                "#0000ff",  # blue
            ]
            bar_w = w / len(bars)
            for i, col in enumerate(bars):
                x0 = int(i * bar_w)
                x1 = int((i + 1) * bar_w)
                canvas.create_rectangle(x0, 0, x1, int(h * 0.65), fill=col, outline="")
            # Middle row: grayscale ramp
            steps = 16
            y0 = int(h * 0.65)
            y1 = int(h * 0.85)
            for i in range(steps):
                g = int(255 * i / (steps - 1))
                col = f"#{g:02x}{g:02x}{g:02x}"
                x0 = int(w * i / steps)
                x1 = int(w * (i + 1) / steps)
                canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
            # Bottom row: saturated patches
            patches = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"]
            p_h = h - y1
            p_w = w / len(patches)
            for i, col in enumerate(patches):
                x0 = int(i * p_w)
                x1 = int((i + 1) * p_w)
                canvas.create_rectangle(x0, y1, x1, h, fill=col, outline="#101010")

        canvas.bind("<Configure>", lambda e: draw_pattern())
        draw_pattern()
    
    def update_audio_visualization(self, levels):
        """Update audio level visualization"""
        # This is often called from background threads
        # Throttle at the source to ~25 FPS to avoid flooding UI queue
        now = time.monotonic()
        if not hasattr(self, '_last_viz_callback_time'):
            self._last_viz_callback_time = 0
            
        if now - self._last_viz_callback_time < 0.04:
            return
        self._last_viz_callback_time = now
        
        self.root.after(0, self._update_audio_visualization_main_thread, levels)

    def _update_audio_visualization_main_thread(self, levels):
        """Update audio level visualization on main thread"""
        if not hasattr(self, 'audio_canvas'):
            return
        
        # Draw bars
        c = self.audio_canvas
        c.delete("all")
        width = self.audio_canvas.winfo_width() or 400
        height = self.audio_canvas.winfo_height() or 80
        # Choose source based on viz mode
        mode = getattr(self, 'viz_mode_var', None).get() if hasattr(self, 'viz_mode_var') else 'levels'
        if mode == 'spectrum' and hasattr(self, 'audio_processor'):
            src = getattr(self.audio_processor, 'viz_spectrum', [])
        else:
            src = levels

        src_len = len(src)
        if src_len == 0:
            return
        # Determine desired bar count from UI
        try:
            desired_bars = max(10, min(80, int(self.viz_bars_var.get())))
        except Exception:
            desired_bars = src_len

        # Resample levels to desired bar count via linear interpolation
        if desired_bars != src_len and desired_bars > 1 and src_len > 1:
            resampled = []
            for i in range(desired_bars):
                pos = i * (src_len - 1) / (desired_bars - 1)
                j = int(pos)
                frac = pos - j
                if j + 1 < src_len:
                    val = src[j] * (1 - frac) + src[j + 1] * frac
                else:
                    val = src[j]
                resampled.append(val)
            src = resampled
        num_bars = len(src)
        bar_width = width / num_bars

        # Apply a visual gain based on current sensitivity to make bars clearer
        try:
            vis_gain = float(self.viz_gain_var.get())
        except Exception:
            vis_gain = 2.0

        # Initialize/maintain per-bar peak hold with decay
        if not hasattr(self, '_bar_peaks') or len(self._bar_peaks) != num_bars:
            self._bar_peaks = [0.0] * num_bars

        decay = 0.04  # fall speed for the peak marker
        min_visible = 2  # px
        for i, level in enumerate(src):
            lvl = min(1.0, max(0.0, float(level) * vis_gain))
            x1, x2 = i * bar_width, (i + 1) * bar_width - 2
            bar_height = max(min_visible, int(lvl * height)) if lvl > 0 else 0
            y1, y2 = height - bar_height, height

            color = "#ff0000" if lvl > 0.7 else "#ffff00" if lvl > 0.4 else "#00ff00"
            if bar_height > 0:
                self.audio_canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

            # Update and draw peak hold (small horizontal line)
            self._bar_peaks[i] = max(self._bar_peaks[i] - decay, lvl)
            peak_y = int(height - self._bar_peaks[i] * height)
            if 0 <= peak_y < height:
                self.audio_canvas.create_rectangle(x1, peak_y, x2, peak_y + 2, fill="#ff66aa", outline="")

        # Update sensitivity label
        try:
            s = float(self.beat_sensitivity.get())
        except Exception:
            s = 2.5
        label = "Low" if s < 2 else "Medium" if s < 4.5 else "High" if s < 6.5 else "Extreme"
        if hasattr(self, 'sens_label_var'):
            self.sens_label_var.set(f"Sensitivity: {label}")
    
    def update_bpm_display(self, bpm):
        """Update BPM display"""
        self.root.after(0, self._update_bpm_display_main_thread, bpm)

    def _update_bpm_display_main_thread(self, bpm):
        """Update BPM display on main thread"""
        if hasattr(self, 'bpm_label'):
            self.bpm_label.config(text=f"BPM: {bpm}")

    def _reset_effect_buttons(self, excluding=None):
        """Reset all effect button labels to 'Start' text"""
        if excluding != 'rainbow' and hasattr(self, 'rainbow_btn'):
            self.rainbow_btn.config(text="Start Rainbow 🌈")
        if excluding != 'blinker' and hasattr(self, 'blinker_btn'):
            self.blinker_btn.config(text="Start Blinker 🎉")
        if excluding != 'strobe' and hasattr(self, 'strobe_btn'):
            self.strobe_btn.config(text="Start Strobe ⚡")
        if excluding != 'white_strobe' and hasattr(self, 'white_strobe_btn'):
            self.white_strobe_btn.config(text="Start White Strobe ⚡")
        if excluding != 'music' and hasattr(self, 'mic_btn'):
            self.mic_btn.config(text="Start Music Sync 🎤")
        if excluding != 'ambi' and hasattr(self, 'ambi_btn'):
            self.ambi_btn.config(text="Start Screen Sync 🖥️")
        if excluding != 'smart_ambient' and hasattr(self, 'smart_ambi_btn'):
            self.smart_ambi_btn.config(text="Start Smart Ambient 🎯")
    
    def on_mode_change(self):
        """Handle light mode change"""
        self.device_manager.set_mode(self.mode_var.get())
        self.effects_engine.stop_all_effects()
    
    def on_brightness_change(self, event):
        """Handle brightness change"""
        self.device_manager.set_brightness(int(self.brightness_var.get()))
    
    def on_temp_change(self, event):
        """Handle temperature change"""
        self.device_manager.set_temperature(int(self.temp_var.get()))
    
    def on_color_brightness_change(self, event):
        """Handle color brightness change"""
        # Update effects engine stored brightness
        self.effects_engine.color_brightness = self.color_bright_var.get()
        # If we're on static color, apply brightness immediately using last HSV
        try:
            v = float(self.color_bright_var.get()) / 1000.0
        except Exception:
            v = 1.0
        if hasattr(self.effects_engine, 'last_hsv') and self.effects_engine.last_hsv:
            h, s, _ = self.effects_engine.last_hsv
            r, g, b = colorsys.hsv_to_rgb(h, s, max(0.0, min(1.0, v)))
            self.device_manager.set_color(r*255, g*255, b*255)
            hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
            if hasattr(self, 'color_preview'):
                self.color_preview.config(bg=hex_color)
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose Lamp Color")
        if color and color[1]:
            self.effects_engine.set_color_from_hex(color[1], self.color_bright_var.get() / 1000.0)
    
    def update_rainbow_preview(self):
        """Update rainbow effect preview"""
        if not hasattr(self, 'rainbow_canvas'):
            return
        
        self.rainbow_canvas.delete("all")
        
        h_min = self.rainbow_h_min.get()
        h_max = self.rainbow_h_max.get()
        width = self.rainbow_canvas.winfo_width() or 400
        
        import colorsys
        for x in range(width):
            hue = h_min + (h_max - h_min) * (x / width)
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
            self.rainbow_canvas.create_line(x, 0, x, 40, fill=color)
    
    def toggle_rainbow(self):
        """Toggle rainbow effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if self.effects_engine.rainbow_running:
            self.effects_engine.stop_rainbow_effect()
            self.rainbow_btn.config(text="Start Rainbow 🌈")
        else:
            # Update rainbow parameters
            self.effects_engine.set_rainbow_parameters(
                speed=self.rainbow_speed_var.get(),
                h_min=self.rainbow_h_min.get(),
                h_max=self.rainbow_h_max.get()
            )
            self.effects_engine.start_rainbow_effect()
            self.rainbow_btn.config(text="Stop Rainbow 🛑")
            self._reset_effect_buttons('rainbow')
            
    def toggle_blinker(self):
        """Toggle blinker effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if self.effects_engine.blinker_running:
            self.effects_engine.stop_blinker_effect()
            self.blinker_btn.config(text="Start Blinker 🎉")
        else:
            self.effects_engine.set_blinker_parameters(
                speed=self.blinker_speed_var.get()
            )
            self.effects_engine.start_blinker_effect()
            self.blinker_btn.config(text="Stop Blinker 🛑")
            self._reset_effect_buttons('blinker')

    def update_blinker_parameters(self):
        """Update blinker parameters live"""
        if self.effects_engine.blinker_running:
            self.effects_engine.set_blinker_parameters(
                speed=self.blinker_speed_var.get()
            )
    
    def toggle_strobe(self):
        """Toggle strobe effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if self.effects_engine.strobe_running:
            self.effects_engine.stop_strobe_effect()
            self.strobe_btn.config(text="Start Strobe ⚡")
        else:
            self.effects_engine.set_strobe_parameters(
                speed=self.strobe_speed_var.get()
            )
            self.effects_engine.start_strobe_effect()
            self.strobe_btn.config(text="Stop Strobe 🛑")
            self._reset_effect_buttons('strobe')

    def update_strobe_parameters(self):
        """Update strobe parameters live"""
        if self.effects_engine.strobe_running:
            self.effects_engine.set_strobe_parameters(
                speed=self.strobe_speed_var.get()
            )
    
    def toggle_white_strobe(self):
        """Toggle white strobe effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if self.effects_engine.white_strobe_running:
            self.effects_engine.stop_white_strobe_effect()
            self.white_strobe_btn.config(text="Start White Strobe ⚡")
        else:
            self.effects_engine.set_white_strobe_parameters(
                speed=self.white_strobe_speed_var.get()
            )
            self.effects_engine.start_white_strobe_effect()
            self.white_strobe_btn.config(text="Stop White Strobe 🛑")
            self._reset_effect_buttons('white_strobe')

    def update_white_strobe_parameters(self):
        """Update white strobe parameters live"""
        if self.effects_engine.white_strobe_running:
            self.effects_engine.set_white_strobe_parameters(
                speed=self.white_strobe_speed_var.get()
            )
    
    def on_set_scene(self, scene_data: str):
        """Set lamp to a hardware scene"""
        self.effects_engine.stop_all_effects()
        self.device_manager.set_scene(scene_data)
        # Reset selection buttons to avoid confusion
        self._reset_effect_buttons()
        self.mode_var.set("scene")
    
    def on_audio_device_change(self, event):
        """Handle audio device change"""
        sel_idx = self.device_combo.current()
        if sel_idx >= 0:
            dev_id = self.audio_processor.audio_devices[sel_idx][0]
            self.audio_processor.set_device(dev_id)
            # If music sync is running, request an in-place restart
            if self.audio_processor.mic_running:
                self.audio_processor.restart()

    def restart_audio_service(self):
        """User-triggered restart of the audio listening service"""
        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "PyAudio not available")
            return
        self.audio_processor.restart()
    
    def toggle_audio_sync(self):
        """Toggle audio synchronization"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "PyAudio not available")
            return
        
        if self.audio_processor.mic_running:
            self.audio_processor.stop_listening()
            self.effects_engine.stop_audio_effect()
            self.mic_btn.config(text="Start Music Sync 🎤")
        else:
            # Update audio parameters
            self.effects_engine.set_audio_parameters(
                mode=self.audio_mode.get(),
                sensitivity=self.beat_sensitivity.get(),
                brightness=int(self.color_bright_var.get())
            )
            
            # Start audio processing
            if self.audio_processor.start_listening():
                self.effects_engine.start_audio_effect()
                self.mic_btn.config(text="Stop Music Sync 🛑")
                self._reset_effect_buttons('music')

    def on_sensitivity_change(self):
        """Apply sensitivity changes live to effects engine"""
        if AUDIO_AVAILABLE and self.audio_processor.mic_running:
            self.effects_engine.set_audio_parameters(
                mode=self.audio_mode.get(),
                sensitivity=self.beat_sensitivity.get(),
                brightness=int(self.color_bright_var.get())
            )

    def toggle_ambilight(self):
        """Toggle screen sync (Ambilight) effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
            
        if not AMBILIGHT_AVAILABLE:
            messagebox.showerror("Ambilight Error", "Ambilight dependencies (mss, cv2) not available")
            return

        if self.effects_engine.ambilight_running:
            self.effects_engine.stop_ambilight_effect()
            self.ambi_btn.config(text="Start Screen Sync 🖥️")
        else:
            self.effects_engine.set_ambilight_parameters(
                alpha=self.ambi_alpha_var.get(),
                monitor_index=self.monitor_combo.current() + 1,
                crop_percent=self.ambi_crop_var.get()
            )
            self.effects_engine.start_ambilight_effect()
            self.ambi_btn.config(text="Stop Screen Sync 🛑")
            self._reset_effect_buttons('ambi')

    def on_ambilight_smoothing_change(self):
        """Update ambilight smoothing live"""
        if self.effects_engine.ambilight_running:
            self.effects_engine.set_ambilight_parameters(
                alpha=self.ambi_alpha_var.get()
            )

    def on_ambilight_crop_change(self):
        """Update ambilight crop live"""
        if self.effects_engine.ambilight_running:
            self.effects_engine.set_ambilight_parameters(
                crop_percent=self.ambi_crop_var.get()
            )

    def on_ambilight_monitor_change(self):
        """Update monitor selection live"""
        if self.effects_engine.ambilight_running:
            self.effects_engine.set_ambilight_parameters(
                monitor_index=self.monitor_combo.current() + 1
            )

    def on_ambilight_mode_change(self):
        """Update color strategy live"""
        # Mode control not available in simplified UI; no-op
        return
    
    def toggle_smart_ambient(self):
        """Toggle Smart Ambient effect"""
        if not self.device_manager.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if self.effects_engine.smart_ambient_running:
            self.effects_engine.stop_smart_ambient_effect()
            self.smart_ambi_btn.config(text="Start Smart Ambient 🎯")
            self.smart_status_var.set("Smart ambient lighting stopped")
        else:
            # Set parameters before starting
            self.effects_engine.set_smart_ambient_parameters(
                monitor_index=self.smart_monitor_combo.current() + 1,
                update_interval=self.smart_interval_var.get()
            )
            
            success = self.effects_engine.start_smart_ambient_effect()
            if success:
                self.smart_ambi_btn.config(text="Stop Smart Ambient 🛑")
                self._reset_effect_buttons('smart_ambient')
            else:
                messagebox.showerror("Smart Ambient Error", "Failed to start smart ambient lighting. Check that screen capture dependencies are installed.")
    
    def on_smart_interval_change(self):
        """Update smart ambient interval live"""
        if self.effects_engine.smart_ambient_running:
            self.effects_engine.set_smart_ambient_parameters(
                update_interval=self.smart_interval_var.get()
            )
    
    def on_smart_monitor_change(self):
        """Update smart ambient monitor selection live"""
        if self.effects_engine.smart_ambient_running:
            self.effects_engine.set_smart_ambient_parameters(
                monitor_index=self.smart_monitor_combo.current() + 1
            )
    
    def on_smart_ambient_status(self, status: str):
        """Handle smart ambient status updates"""
        self.smart_status_var.set(status)
    
    def on_turn_on(self):
        """Turn on the lamp and reset UI"""
        self.device_manager.turn_on()
        self.status_var.set("Turned ON ✅")

    def on_turn_off(self):
        """Stop all effects and turn off the lamp with priority"""
        # Stop all effect generation first
        self.effects_engine.stop_all_effects()
        self._reset_effect_buttons(None)
        
        # Stop audio if running
        if AUDIO_AVAILABLE and self.audio_processor.mic_running:
            self.audio_processor.stop_listening()
            self.mic_btn.config(text="Start Music Sync 🎤")
            
        # Send priority OFF command
        self.device_manager.turn_off()
        self.status_var.set("Turned OFF 🌑")

    def on_close(self):
        """Handle application close"""
        self.logger.info("Closing application...")
        
        # Stop all effects
        self.effects_engine.cleanup()
        
        # Stop audio processing
        self.audio_processor.cleanup()
        # Stop API server
        try:
            if hasattr(self, 'api_httpd') and self.api_httpd:
                self.api_httpd.shutdown()
                self.api_httpd.server_close()
        except Exception:
            pass
        
        # Close device connection
        self.device_manager.close()
        
        # Save configuration
        self.config.save()
        
        # Destroy window
        self.root.destroy()
        
        self.logger.info("Application closed successfully")

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
