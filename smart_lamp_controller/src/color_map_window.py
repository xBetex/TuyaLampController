#!/usr/bin/env python3
"""
Color Map Window - Separate window for color selection and prevalence analysis
"""

import tkinter as tk
from tkinter import ttk, colorchooser
from collections import deque
from color_selection_logic import ColorSelectionLogic, SCREEN_CAPTURE_AVAILABLE
from smart_ambient_processor import SmartAmbientProcessor
from color_history import HIST


class ColorMapWindow:
    """Separate window for color map functionality"""

    def __init__(self, parent, device_manager, effects_engine):
        self.parent = parent
        self.device_manager = device_manager
        self.effects_engine = effects_engine

        # Initialize color logic
        self.color_logic = ColorSelectionLogic()

        # Initialize smart ambient processor
        self.smart_ambient = SmartAmbientProcessor()
        self.live_mode = False

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Ambilight Cover Adjust")
        self.window.geometry("1200x800")
        self.window.resizable(True, True)

        # Make window stay on top initially
        self.window.transient(parent)

        # Setup UI
        self.setup_ui()

        # Initialize
        self.populate_monitor_list()
        self.refresh_timer = None
        self.auto_refresh_var = tk.BooleanVar(value=True)
        self.tolerance_var = tk.DoubleVar(value=0.15)

        # Start auto-refresh
        self.start_auto_refresh()

        # Create color map after window is shown
        self.window.after(200, self.create_color_map)

        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Center window
        self.center_window()

    def setup_ui(self):
        """Setup the UI layout"""
        # Scrollable container (prevents layout issues on smaller screens)
        container = ttk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True)

        self._scroll_canvas = tk.Canvas(container, highlightthickness=0)
        vscroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self._scroll_canvas.yview)
        hscroll = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self._scroll_canvas.xview)
        self._scroll_canvas.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        # Pack: canvas expands, vscroll on right, hscroll on bottom
        self._scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Frame inside canvas that will hold all content
        content_holder = ttk.Frame(self._scroll_canvas)
        self._scroll_canvas.create_window((0, 0), window=content_holder, anchor="nw")

        # Update scrollregion when content changes size
        def _on_frame_configure(event):
            self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

        content_holder.bind("<Configure>", _on_frame_configure)

        # Enable mouse wheel scrolling on Windows
        def _on_mouse_wheel(event):
            try:
                self._scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

        self._scroll_canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
        # Side scroll with Shift+Wheel
        def _on_shift_wheel(event):
            try:
                self._scroll_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
            return "break"
        self._scroll_canvas.bind_all("<Shift-MouseWheel>", _on_shift_wheel)

        # Main container with padding inside scrollable area
        main_frame = ttk.Frame(content_holder, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            header_frame,
            text="Ambilight Cover Adjust",
            font=("Segoe UI", 14, "bold"),
        ).pack(side=tk.LEFT)

        # Close button
        ttk.Button(header_frame, text="Close", command=self.on_close).pack(
            side=tk.RIGHT
        )

        # Description
        desc_label = ttk.Label(
            header_frame,
            text="Select colors and analyze their prevalence on your screen for optimal ambient lighting",
            font=("Segoe UI", 9),
            foreground="#666666",
        )
        desc_label.pack(side=tk.LEFT, padx=(20, 0))

        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left side - Color map
        left_frame = ttk.LabelFrame(
            content_frame, text="Color Selection Map", padding="15"
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # Color map canvas - large
        self.color_map_canvas = tk.Canvas(
            left_frame, width=400, height=300, bg="white", relief="sunken", bd=2
        )
        self.color_map_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.color_map_canvas.bind("<Button-1>", self.on_color_map_click)
        self.color_map_canvas.bind("<B1-Motion>", self.on_color_map_drag)

        # Color map controls
        map_controls = ttk.Frame(left_frame)
        map_controls.pack(fill=tk.X)

        ttk.Button(
            map_controls, text="Custom Color 🎨", command=self.choose_custom_color
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            map_controls, text="Reset to Center", command=self.reset_selection
        ).pack(side=tk.LEFT)

        # Middle - Preview and analysis
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        # Top right - Monitor preview
        preview_frame = ttk.LabelFrame(
            right_frame, text="Screen Prevalence Analysis", padding="15"
        )
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        # Zoom factor and ROI for analysis
        self.zoom_var = tk.DoubleVar(value=1.0)
        self._roi_norm = None  # (x0, y0, x1, y1) normalized to full image
        self._roi_rect_id = None
        self._view_center_norm = (0.5, 0.5)  # center of zoom window in full image space
        self._view_window_norm = None  # (vx0, vy0, vx1, vy1) of current displayed window in full image space
        self._drag_mode = None  # 'creating', 'moving', 'resizing', 'panning'
        self._drag_start = None  # (xn, yn) in full image norm or canvas px for panning
        self._roi_handles = []  # handle ids

        self.preview_canvas = tk.Canvas(
            preview_frame, width=320, height=240, bg="#1a1a1a", relief="sunken", bd=2
        )
        self.preview_canvas.pack(pady=(0, 10))
        # ROI selection bindings
        self.preview_canvas.bind("<Button-1>", self._on_preview_press)
        self.preview_canvas.bind("<B1-Motion>", self._on_preview_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self._on_preview_release)
        # Pan with right mouse
        self.preview_canvas.bind("<Button-3>", self._on_pan_press)
        self.preview_canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.preview_canvas.bind("<ButtonRelease-3>", self._on_pan_release)
        # Cursor feedback and wheel zoom
        self.preview_canvas.bind("<Motion>", self._on_preview_motion)
        self.preview_canvas.bind("<MouseWheel>", self._on_wheel_zoom)

        # Preview controls in a more compact layout
        controls_grid = ttk.Frame(preview_frame)
        controls_grid.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Monitor and Live toggle
        ttk.Label(controls_grid, text="Monitor:", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky=tk.W
        )

        self.monitor_var = tk.StringVar(value="Monitor 1")
        self.monitor_combo = ttk.Combobox(
            controls_grid,
            textvariable=self.monitor_var,
            state="readonly",
            width=15,
            font=("Segoe UI", 9),
        )
        self.monitor_combo.grid(row=0, column=1, padx=(5, 10), sticky=tk.W)
        self.monitor_combo.bind("<<ComboboxSelected>>", self.on_monitor_change)

        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls_grid,
            text="Live Preview",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh,
        ).grid(row=0, column=2, padx=(5, 0))

        # Row 2: Zoom slider
        ttk.Label(controls_grid, text="Zoom:").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        zoom_scale = ttk.Scale(
            controls_grid,
            from_=1.0,
            to=4.0,
            variable=self.zoom_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_preview(),
        )
        zoom_scale.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=(6, 0))
        controls_grid.columnconfigure(1, weight=1)

        # Clear Selection button
        ttk.Button(preview_frame, text="Clear Selection", command=self._clear_roi).pack(anchor=tk.E, pady=(0, 5))

        # Prevalence info - simplified
        self.prevalence_var = tk.StringVar(
            value="Click 'Auto-Select Best Color' for smart selection"
        )
        prevalence_label = ttk.Label(
            preview_frame,
            textvariable=self.prevalence_var,
            font=("Segoe UI", 9),
            foreground="#333333",
            wraplength=300,
        )
        prevalence_label.pack(anchor=tk.W, pady=(0, 10))

        # Bottom right - Color info and controls in columns
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)

        # Left column - Selected color
        left_col = ttk.Frame(bottom_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        color_info_frame = ttk.LabelFrame(left_col, text="Selected Color", padding="10")
        color_info_frame.pack(fill=tk.X, pady=(0, 10))

        # Color display
        self.color_display = tk.Label(
            color_info_frame, text="", bg="#ff0000", height=2, relief="sunken", bd=2
        )
        self.color_display.pack(fill=tk.X, pady=(0, 5))

        # Color hex
        self.color_info_var = tk.StringVar(value="#FF0000")
        ttk.Label(
            color_info_frame,
            textvariable=self.color_info_var,
            font=("Consolas", 11, "bold"),
        ).pack(anchor=tk.W)

        # Color analysis - simplified
        analysis_frame = ttk.LabelFrame(left_col, text="Color Info", padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True)

        self.analysis_var = tk.StringVar(value="Select a color to see basic info")
        analysis_label = ttk.Label(
            analysis_frame,
            textvariable=self.analysis_var,
            font=("Segoe UI", 9),
            wraplength=200,
            justify=tk.LEFT,
        )
        analysis_label.pack(fill=tk.BOTH, expand=True)

        # Right column - Dominant colors and best color
        right_col = ttk.Frame(bottom_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        dominant_frame = ttk.LabelFrame(
            right_col, text="Screen Accent Colors", padding="10"
        )
        dominant_frame.pack(fill=tk.BOTH, expand=True)

        # Live mode checkbox
        self.live_var = tk.BooleanVar(value=False)
        self.live_checkbox = ttk.Checkbutton(
            dominant_frame,
            text="🔴 Live - Use Screen Accent Colors",
            variable=self.live_var,
            command=self.toggle_live_mode,
        )
        self.live_checkbox.pack(fill=tk.X, pady=(0, 5))

        # Best color button
        self.best_color_btn = ttk.Button(
            dominant_frame,
            text="🎯 Auto-Select Best Color",
            command=self.select_best_color,
        )
        self.best_color_btn.pack(fill=tk.X, pady=(0, 10))

        self.dominant_colors_frame = ttk.Frame(dominant_frame)
        self.dominant_colors_frame.pack(fill=tk.X)

        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            action_frame,
            text="Apply Color to Lamp 💡",
            command=self.apply_color,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            action_frame,
            text="Sample Screen Color 🎯",
            command=self.sample_screen_color,
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Status
        self.status_var = tk.StringVar(value="Ready - Select a color from the map")
        ttk.Label(
            action_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 9, "italic"),
            foreground="#666666",
        ).pack(side=tk.RIGHT)

        # Right column - History and Live Simulation
        history_col = ttk.Frame(content_frame)
        history_col.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Live Simulation (lamp)
        sim_frame = ttk.LabelFrame(history_col, text="Live Simulation", padding="10")
        sim_frame.pack(fill=tk.X, pady=(0, 10))
        self.sim_canvas = tk.Canvas(sim_frame, width=120, height=120, bg="#111111", highlightthickness=0)
        self.sim_canvas.pack()
        self.sim_bulb = self.sim_canvas.create_oval(10, 10, 110, 110, fill="#000000", outline="#333333", width=2)

        # History visibility toggle
        self.history_visible_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(history_col, text="Show History", variable=self.history_visible_var, command=self.toggle_history_visibility).pack(anchor=tk.W, pady=(0, 5))

        # History panel with vertical + horizontal scrollbar
        history_frame = ttk.LabelFrame(history_col, text="History", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True)
        self.history_frame = history_frame

        history_container = ttk.Frame(history_frame)
        history_container.pack(fill=tk.BOTH, expand=True)

        self.history_text = tk.Text(
            history_container,
            height=8,
            wrap="none",
            font=("Consolas", 9),
            width=24,
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        history_scrollbar = ttk.Scrollbar(
            history_container, orient=tk.VERTICAL, command=self.history_text.yview
        )
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.configure(yscrollcommand=history_scrollbar.set)

        # Horizontal scrollbar
        hscroll = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=self.history_text.xview)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.history_text.configure(xscrollcommand=hscroll.set)

        # Side scroll with Shift+MouseWheel
        def _on_history_shift_wheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
            except Exception:
                delta = -1
            self.history_text.xview_scroll(delta, "units")
            return "break"
        self.history_text.bind("<Shift-MouseWheel>", _on_history_shift_wheel)

        # Keep only the last N history entries (ring buffer)
        self.history_buffer = deque(maxlen=10)

        # Subscribe to global color history updates
        try:
            HIST.subscribe(self._on_history_update)
        except Exception:
            pass

        # 5-second rolling history section
        recent_frame = ttk.LabelFrame(history_col, text="Last 5 seconds", padding="10")
        recent_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.recent_text = tk.Text(
            recent_frame,
            height=6,
            wrap="none",
            font=("Consolas", 9),
            width=24,
        )
        self.recent_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        recent_vscroll = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_text.yview)
        recent_vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_text.configure(yscrollcommand=recent_vscroll.set)
        recent_hscroll = ttk.Scrollbar(recent_frame, orient=tk.HORIZONTAL, command=self.recent_text.xview)
        recent_hscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.recent_text.configure(xscrollcommand=recent_hscroll.set)

        # Shift+MouseWheel horizontal scroll for recent history
        def _on_recent_shift_wheel(event):
            try:
                delta = int(-1 * (event.delta / 120))
            except Exception:
                delta = -1
            self.recent_text.xview_scroll(delta, "units")
            return "break"
        self.recent_text.bind("<Shift-MouseWheel>", _on_recent_shift_wheel)

    def toggle_history_visibility(self):
        if self.history_visible_var.get():
            try:
                self.history_frame.pack(fill=tk.BOTH, expand=True)
            except Exception:
                pass
        else:
            try:
                self.history_frame.forget()
            except Exception:
                pass

    def center_window(self):
        """Center the window on screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def create_color_map(self):
        """Create a simple RGB color selection using gradients"""
        width = self.color_map_canvas.winfo_width() or 400
        height = self.color_map_canvas.winfo_height() or 300

        try:
            from PIL import Image, ImageTk, ImageDraw

            # Create RGB color gradient image
            img = Image.new("RGB", (width, height))
            draw = ImageDraw.Draw(img)

            # Create a simple HSV to RGB gradient
            for x in range(width):
                for y in range(height):
                    # Map x to hue (0-360), y to saturation/value
                    hue = (x / width) * 360
                    saturation = 1.0 - (y / height) * 0.3  # Keep high saturation
                    value = 1.0 - (y / height) * 0.5  # Vary brightness

                    # Convert HSV to RGB
                    import colorsys

                    r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation, value)
                    color = (int(r * 255), int(g * 255), int(b * 255))

                    img.putpixel((x, y), color)

            # Convert to PhotoImage and display
            self.color_map_image = ImageTk.PhotoImage(img)
            self.color_map_canvas.create_image(
                0, 0, anchor=tk.NW, image=self.color_map_image
            )

        except ImportError:
            # Fallback: Create simple color blocks
            self.create_simple_color_blocks(width, height)

        # Add selection indicator
        center_x = width // 2
        center_y = height // 2

        self.selection_indicator = self.color_map_canvas.create_oval(
            center_x - 10,
            center_y - 10,
            center_x + 10,
            center_y + 10,
            outline="white",
            width=4,
            fill="",
            tags="selection",
        )

        self.selection_inner = self.color_map_canvas.create_oval(
            center_x - 6,
            center_y - 6,
            center_x + 6,
            center_y + 6,
            outline="black",
            width=2,
            fill="",
            tags="selection",
        )

        # Initialize preview
        self.update_preview()

    def create_simple_color_blocks(self, width, height):
        """Fallback: Create simple color blocks when PIL is not available"""
        # Create a simple grid of color blocks
        block_width = width // 12
        block_height = height // 8

        colors = [
            # Row 1 - Reds
            "#ff0000",
            "#ff3333",
            "#ff6666",
            "#ff9999",
            "#ffcccc",
            "#ff0033",
            "#ff0066",
            "#ff0099",
            "#ff00cc",
            "#ff00ff",
            "#cc00ff",
            "#9900ff",
            # Row 2 - Oranges/Yellows
            "#ff3300",
            "#ff6600",
            "#ff9900",
            "#ffcc00",
            "#ffff00",
            "#ccff00",
            "#99ff00",
            "#66ff00",
            "#33ff00",
            "#00ff00",
            "#00ff33",
            "#00ff66",
            # Row 3 - Greens
            "#00ff99",
            "#00ffcc",
            "#00ffff",
            "#00ccff",
            "#0099ff",
            "#0066ff",
            "#0033ff",
            "#0000ff",
            "#3300ff",
            "#6600ff",
            "#9900cc",
            "#cc0099",
            # Row 4 - Blues
            "#ff0066",
            "#ff3366",
            "#ff6666",
            "#ff9966",
            "#ffcc66",
            "#ffff66",
            "#ccff66",
            "#99ff66",
            "#66ff66",
            "#33ff66",
            "#00ff66",
            "#00ff99",
            # Row 5 - Purples
            "#6600cc",
            "#9900ff",
            "#cc00ff",
            "#ff00cc",
            "#ff0099",
            "#ff0066",
            "#ff0033",
            "#ff3300",
            "#ff6600",
            "#ff9900",
            "#ffcc00",
            "#ffff00",
            # Row 6 - More variety
            "#cccccc",
            "#999999",
            "#666666",
            "#333333",
            "#000000",
            "#ffffff",
            "#ffcccc",
            "#ccffcc",
            "#ccccff",
            "#ffffcc",
            "#ffccff",
            "#ccffff",
            # Row 7 - Pastels
            "#ffdddd",
            "#ddffdd",
            "#ddddff",
            "#ffffdd",
            "#ffddff",
            "#ddffff",
            "#ffeedd",
            "#eeffdd",
            "#ddeeff",
            "#ffeeee",
            "#eeffee",
            "#eeeeff",
            # Row 8 - Dark tones
            "#800000",
            "#008000",
            "#000080",
            "#808000",
            "#800080",
            "#008080",
            "#404040",
            "#804040",
            "#408040",
            "#404080",
            "#808040",
            "#804080",
        ]

        for i, color in enumerate(colors):
            row = i // 12
            col = i % 12
            if row >= 8:  # Don't exceed canvas height
                break

            x1 = col * block_width
            y1 = row * block_height
            x2 = x1 + block_width
            y2 = y1 + block_height

            self.color_map_canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                outline="#cccccc",
                width=1,
                tags="color_block",
            )

    def on_color_map_click(self, event):
        """Handle click on color map"""
        self.update_selection_from_click(event.x, event.y)

    def on_color_map_drag(self, event):
        """Handle drag on color map"""
        self.update_selection_from_click(event.x, event.y)

    def update_selection_from_click(self, x: int, y: int):
        """Update color selection from click coordinates"""
        width = self.color_map_canvas.winfo_width() or 400
        height = self.color_map_canvas.winfo_height() or 300

        # Clamp coordinates
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))

        # Get color from coordinates using the same logic as image creation
        if hasattr(self, "color_map_image"):
            # If we have PIL, get color from the image
            try:
                from PIL import Image, ImageTk

                # Get the color from the image
                hue = (x / width) * 360
                saturation = 1.0 - (y / height) * 0.3
                value = 1.0 - (y / height) * 0.5

                import colorsys

                r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation, value)
                color = "#{:02x}{:02x}{:02x}".format(
                    int(r * 255), int(g * 255), int(b * 255)
                )
            except ImportError:
                color = self.get_color_from_blocks(x, y, width, height)
        else:
            # Fallback to block-based color selection
            color = self.get_color_from_blocks(x, y, width, height)

        position = (x / width, y / height)

        # Update logic
        self.color_logic.update_selection(color, position)

        # Update UI
        self.update_selection_indicator(x, y)
        self.update_color_info()
        self.update_preview()

    def get_color_from_blocks(self, x: int, y: int, width: int, height: int) -> str:
        """Get color from color blocks (fallback method)"""
        block_width = width // 12
        block_height = height // 8

        col = min(11, x // block_width)
        row = min(7, y // block_height)

        colors = [
            # Row 1 - Reds
            "#ff0000",
            "#ff3333",
            "#ff6666",
            "#ff9999",
            "#ffcccc",
            "#ff0033",
            "#ff0066",
            "#ff0099",
            "#ff00cc",
            "#ff00ff",
            "#cc00ff",
            "#9900ff",
            # Row 2 - Oranges/Yellows
            "#ff3300",
            "#ff6600",
            "#ff9900",
            "#ffcc00",
            "#ffff00",
            "#ccff00",
            "#99ff00",
            "#66ff00",
            "#33ff00",
            "#00ff00",
            "#00ff33",
            "#00ff66",
            # Row 3 - Greens
            "#00ff99",
            "#00ffcc",
            "#00ffff",
            "#00ccff",
            "#0099ff",
            "#0066ff",
            "#0033ff",
            "#0000ff",
            "#3300ff",
            "#6600ff",
            "#9900cc",
            "#cc0099",
            # Row 4 - Blues
            "#ff0066",
            "#ff3366",
            "#ff6666",
            "#ff9966",
            "#ffcc66",
            "#ffff66",
            "#ccff66",
            "#99ff66",
            "#66ff66",
            "#33ff66",
            "#00ff66",
            "#00ff99",
            # Row 5 - Purples
            "#6600cc",
            "#9900ff",
            "#cc00ff",
            "#ff00cc",
            "#ff0099",
            "#ff0066",
            "#ff0033",
            "#ff3300",
            "#ff6600",
            "#ff9900",
            "#ffcc00",
            "#ffff00",
            # Row 6 - More variety
            "#cccccc",
            "#999999",
            "#666666",
            "#333333",
            "#000000",
            "#ffffff",
            "#ffcccc",
            "#ccffcc",
            "#ccccff",
            "#ffffcc",
            "#ffccff",
            "#ccffff",
            # Row 7 - Pastels
            "#ffdddd",
            "#ddffdd",
            "#ddddff",
            "#ffffdd",
            "#ffddff",
            "#ddffff",
            "#ffeedd",
            "#eeffdd",
            "#ddeeff",
            "#ffeeee",
            "#eeffee",
            "#eeeeff",
            # Row 8 - Dark tones
            "#800000",
            "#008000",
            "#000080",
            "#808000",
            "#800080",
            "#008080",
            "#404040",
            "#804040",
            "#408040",
            "#404080",
            "#808040",
            "#804080",
        ]

        index = row * 12 + col
        if index < len(colors):
            return colors[index]
        else:
            return "#ff0000"  # Default to red

    def update_selection_indicator(self, x: int, y: int):
        """Update the selection indicator position"""
        self.color_map_canvas.coords(
            self.selection_indicator, x - 10, y - 10, x + 10, y + 10
        )
        self.color_map_canvas.coords(self.selection_inner, x - 6, y - 6, x + 6, y + 6)

    def update_color_info(self):
        """Update color information display"""
        info = self.color_logic.get_selection_info()

        self.color_display.config(bg=info["color"])
        self.color_info_var.set(info["color"].upper())
        self._update_sim_canvas(info["color"])

        # Simple color info
        category = info["category"]
        self.analysis_var.set(
            f"Color: {category}\nHex: {info['color']}\nClick accent colors or use 'Auto-Select Best Color' for smart selection."
        )

    def update_preview(self):
        """Update the preview with screen thumbnail"""
        # If user is actively adjusting the ROI, keep the current image stable and redraw only overlays
        if isinstance(self._drag_mode, (tuple,)) or self._drag_mode in {"creating", "moving", "resizing"}:
            try:
                # Clear previous ROI and handles only
                if self._roi_rect_id:
                    self.preview_canvas.delete(self._roi_rect_id)
                for hid in getattr(self, "_roi_handles", []):
                    try:
                        self.preview_canvas.delete(hid)
                    except Exception:
                        pass
                self._roi_handles = []
                # Redraw ROI overlay in current view
                cw = int(self.preview_canvas.cget('width'))
                ch = int(self.preview_canvas.cget('height'))
                if self._roi_norm is not None and self._view_window_norm is not None:
                    vx0, vy0, vx1, vy1 = self._view_window_norm
                    rw0, rh0, rw1, rh1 = self._roi_norm
                    ix0 = max(vx0, min(vx1, rw0))
                    iy0 = max(vy0, min(vy1, rh0))
                    ix1 = max(vx0, min(vx1, rw1))
                    iy1 = max(vy0, min(vy1, rh1))
                    if ix1 > ix0 and iy1 > iy0:
                        cx0 = int((ix0 - vx0) / (vx1 - vx0) * cw)
                        cy0 = int((iy0 - vy0) / (vy1 - vy0) * ch)
                        cx1 = int((ix1 - vx0) / (vx1 - vx0) * cw)
                        cy1 = int((iy1 - vy0) / (vy1 - vy0) * ch)
                        self._roi_rect_id = self.preview_canvas.create_rectangle(
                            cx0, cy0, cx1, cy1, outline="#00ff88", width=2
                        )
                        self._draw_roi_handles(cx0, cy0, cx1, cy1)
                # Skip full redraw while dragging to avoid image shifting
                return
            except Exception:
                # Fall through to full redraw on any error
                pass

        self.preview_canvas.delete("all")

        # Keep canvas fixed size; zoom controls source crop area
        canvas_width = 320
        canvas_height = 240
        self.preview_canvas.config(width=canvas_width, height=canvas_height)
        zoom = max(1.0, min(4.0, float(self.zoom_var.get()))) if isinstance(self.zoom_var.get(), (int, float)) else 1.0

        # Show screen thumbnail
        thumbnail_tk = self.color_logic.get_screen_thumbnail_tk()

        if thumbnail_tk:
            try:
                from PIL import ImageTk, Image

                full_img = self.color_logic.screen_thumbnail
                if full_img:
                    # Determine view window in full image space based on zoom and center
                    iw, ih = full_img.size
                    # Determine center: keep current view center (do not recenter while selecting)
                    cx, cy = self._view_center_norm
                    # Compute window size in normalized units
                    vw = min(1.0, 1.0 / zoom)
                    vh = min(1.0, 1.0 / zoom)
                    # Preserve aspect ratio of canvas
                    canvas_ar = canvas_width / canvas_height
                    img_ar = iw / ih if ih else 1.0
                    # Adjust vw,vh to canvas aspect within image space
                    if canvas_ar >= 1.0:
                        # canvas wider, constrain height
                        vh = min(vh, 1.0)
                        vw = min(vw, vh * canvas_ar)
                    else:
                        vw = min(vw, 1.0)
                        vh = min(vh, vw / canvas_ar)
                    # Compute window bounds centered at (cx,cy)
                    vx0 = max(0.0, cx - vw / 2.0)
                    vy0 = max(0.0, cy - vh / 2.0)
                    vx1 = min(1.0, cx + vw / 2.0)
                    vy1 = min(1.0, cy + vh / 2.0)
                    # Re-center if clamped reduced span
                    vw_eff = vx1 - vx0
                    vh_eff = vy1 - vy0
                    if vw_eff < vw:
                        # expand left/right if possible
                        shift = (vw - vw_eff) / 2.0
                        vx0 = max(0.0, vx0 - shift)
                        vx1 = min(1.0, vx1 + shift)
                    if vh_eff < vh:
                        shift = (vh - vh_eff) / 2.0
                        vy0 = max(0.0, vy0 - shift)
                        vy1 = min(1.0, vy1 + shift)
                    self._view_window_norm = (vx0, vy0, vx1, vy1)
                    # Map to pixel crop
                    px0 = int(vx0 * iw)
                    py0 = int(vy0 * ih)
                    px1 = int(vx1 * iw)
                    py1 = int(vy1 * ih)
                    px1 = max(px0 + 1, px1)
                    py1 = max(py0 + 1, py1)
                    view_img = full_img.crop((px0, py0, px1, py1))
                    view_img = view_img.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                    thumbnail_tk = ImageTk.PhotoImage(view_img)
            except Exception:
                pass

            self.preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=thumbnail_tk,
                tags="preview",
            )
            self.preview_canvas.thumbnail_ref = thumbnail_tk
        else:
            # Mock screen
            self.preview_canvas.create_rectangle(
                10,
                10,
                canvas_width - 10,
                canvas_height - 10,
                fill="#000000",
                outline="#666666",
                width=2,
                tags="preview",
            )

            self.preview_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="Screen Preview Unavailable\n\nInstall required packages:\npip install mss pillow numpy",
                fill="#666666",
                font=("Segoe UI", 10),
                justify=tk.CENTER,
                tags="preview",
            )

        # Draw ROI if present (transform from full image space to current view window -> canvas)
        if self._roi_norm is not None and self._view_window_norm is not None:
            vx0, vy0, vx1, vy1 = self._view_window_norm
            rw0, rh0, rw1, rh1 = self._roi_norm
            # Compute intersection with view window
            ix0 = max(vx0, min(vx1, rw0))
            iy0 = max(vy0, min(vy1, rh0))
            ix1 = max(vx0, min(vx1, rw1))
            iy1 = max(vy0, min(vy1, rh1))
            # Map to canvas
            if ix1 > ix0 and iy1 > iy0:
                cx0 = int((ix0 - vx0) / (vx1 - vx0) * canvas_width)
                cy0 = int((iy0 - vy0) / (vy1 - vy0) * canvas_height)
                cx1 = int((ix1 - vx0) / (vx1 - vx0) * canvas_width)
                cy1 = int((iy1 - vy0) / (vy1 - vy0) * canvas_height)
                self._roi_rect_id = self.preview_canvas.create_rectangle(
                    cx0, cy0, cx1, cy1, outline="#00ff88", width=2
                )
                # Draw resize handles (small squares at corners)
                self._draw_roi_handles(cx0, cy0, cx1, cy1)

        # Update dominant colors
        self.update_dominant_colors()

    def _on_preview_press(self, event):
        cw = int(self.preview_canvas.cget('width'))
        ch = int(self.preview_canvas.cget('height'))
        x = max(0, min(cw, event.x))
        y = max(0, min(ch, event.y))
        # Map canvas coords to full image normalized via current view window
        if self._view_window_norm is not None:
            vx0, vy0, vx1, vy1 = self._view_window_norm
        else:
            vx0, vy0, vx1, vy1 = (0.0, 0.0, 1.0, 1.0)
        xn = vx0 + (x / cw) * (vx1 - vx0)
        yn = vy0 + (y / ch) * (vy1 - vy0)
        # Determine if pressing on handles or inside ROI for move/resize
        hit_handle = self._hit_test_handle(x, y)
        if hit_handle and self._roi_norm is not None:
            self._drag_mode = ('resizing', hit_handle)
            self._drag_start = (xn, yn)
            return
        if self._roi_norm is not None and self._point_in_roi_norm(xn, yn):
            self._drag_mode = 'moving'
            self._drag_start = (xn, yn)
        else:
            self._drag_mode = 'creating'
            self._roi_norm = (xn, yn, xn, yn)
            self._drag_start = (xn, yn)
        self.update_preview()

    def _on_preview_drag(self, event):
        if self._roi_norm is None:
            return
        cw = int(self.preview_canvas.cget('width'))
        ch = int(self.preview_canvas.cget('height'))
        x = max(0, min(cw, event.x))
        y = max(0, min(ch, event.y))
        # Map canvas coords to full image normalized via current view window
        if self._view_window_norm is not None:
            vx0, vy0, vx1, vy1 = self._view_window_norm
        else:
            vx0, vy0, vx1, vy1 = (0.0, 0.0, 1.0, 1.0)
        xn = vx0 + (x / cw) * (vx1 - vx0)
        yn = vy0 + (y / ch) * (vy1 - vy0)
        if self._drag_mode == 'creating':
            x0, y0, _, _ = self._roi_norm
            x1 = max(min(xn, 1.0), 0.0)
            y1 = max(min(yn, 1.0), 0.0)
            self._roi_norm = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        elif self._drag_mode == 'moving':
            sx, sy = self._drag_start
            dx, dy = xn - sx, yn - sy
            rx0, ry0, rx1, ry1 = self._roi_norm
            # Move ROI, clamp to [0,1]
            w, h = rx1 - rx0, ry1 - ry0
            nx0 = max(0.0, min(1.0 - w, rx0 + dx))
            ny0 = max(0.0, min(1.0 - h, ry0 + dy))
            self._roi_norm = (nx0, ny0, nx0 + w, ny0 + h)
            self._drag_start = (xn, yn)
        elif isinstance(self._drag_mode, tuple) and self._drag_mode[0] == 'resizing':
            corner = self._drag_mode[1]
            rx0, ry0, rx1, ry1 = self._roi_norm
            # Adjust based on corner
            if 'nw' in corner:
                rx0, ry0 = xn, yn
            if 'ne' in corner:
                rx1, ry0 = xn, yn
            if 'sw' in corner:
                rx0, ry1 = xn, yn
            if 'se' in corner:
                rx1, ry1 = xn, yn
            # Normalize
            self._roi_norm = (min(rx0, rx1), min(ry0, ry1), max(rx0, rx1), max(ry0, ry1))
        self.update_preview()

    def _on_preview_release(self, event):
        # End drag; keep current ROI; re-run dominant colors
        self._drag_mode = None
        self._drag_start = None
        self.update_preview()

    def _on_pan_press(self, event):
        self._drag_mode = 'panning'
        self._drag_start = (event.x, event.y)

    def _on_pan_drag(self, event):
        if self._drag_mode != 'panning' or self._view_window_norm is None:
            return
        cw = int(self.preview_canvas.cget('width'))
        ch = int(self.preview_canvas.cget('height'))
        sx, sy = self._drag_start
        dx = (sx - event.x) / cw
        dy = (sy - event.y) / ch
        vx0, vy0, vx1, vy1 = self._view_window_norm
        vw, vh = vx1 - vx0, vy1 - vy0
        # Shift center and clamp
        cx = (vx0 + vx1) / 2.0 + dx
        cy = (vy0 + vy1) / 2.0 + dy
        cx = max(vw / 2.0, min(1.0 - vw / 2.0, cx))
        cy = max(vh / 2.0, min(1.0 - vh / 2.0, cy))
        self._view_center_norm = (cx, cy)
        self._drag_start = (event.x, event.y)
        self.update_preview()

    def _on_pan_release(self, event):
        if self._drag_mode == 'panning':
            self._drag_mode = None
            self._drag_start = None

    def _on_wheel_zoom(self, event):
        # Zoom around cursor
        try:
            delta = event.delta / 120.0
        except Exception:
            delta = 0
        new_zoom = max(1.0, min(4.0, float(self.zoom_var.get()) + 0.1 * delta))
        # Update center to cursor position for intuitive zoom
        cw = int(self.preview_canvas.cget('width'))
        ch = int(self.preview_canvas.cget('height'))
        x = max(0, min(cw, event.x))
        y = max(0, min(ch, event.y))
        if self._view_window_norm is not None:
            vx0, vy0, vx1, vy1 = self._view_window_norm
        else:
            vx0, vy0, vx1, vy1 = (0.0, 0.0, 1.0, 1.0)
        xn = vx0 + (x / cw) * (vx1 - vx0)
        yn = vy0 + (y / ch) * (vy1 - vy0)
        self._view_center_norm = (xn, yn)
        self.zoom_var.set(new_zoom)
        self.update_preview()

    def _on_preview_motion(self, event):
        # Update cursor based on hit testing
        cw = int(self.preview_canvas.cget('width'))
        ch = int(self.preview_canvas.cget('height'))
        x = max(0, min(cw, event.x))
        y = max(0, min(ch, event.y))
        handle = self._hit_test_handle(x, y)
        if handle:
            cursor = {
                'nw': 'top_left_corner',
                'ne': 'top_right_corner',
                'sw': 'bottom_left_corner',
                'se': 'bottom_right_corner',
            }.get(handle, 'tcross')
            self.preview_canvas.config(cursor=cursor)
        elif self._roi_rect_id and self._point_in_roi_canvas(x, y):
            self.preview_canvas.config(cursor='fleur')
        else:
            self.preview_canvas.config(cursor='crosshair')

    def _draw_roi_handles(self, x0, y0, x1, y1):
        # Clear old handles
        for hid in self._roi_handles:
            try:
                self.preview_canvas.delete(hid)
            except Exception:
                pass
        self._roi_handles = []
        size = 6
        corners = {
            'nw': (x0, y0),
            'ne': (x1, y0),
            'sw': (x0, y1),
            'se': (x1, y1),
        }
        for key, (cx, cy) in corners.items():
            hid = self.preview_canvas.create_rectangle(
                cx - size, cy - size, cx + size, cy + size,
                fill="#00ff88", outline="#004433", tags=(f"handle_{key}",)
            )
            self._roi_handles.append(hid)

    def _hit_test_handle(self, x, y):
        # Return handle key if (x,y) falls inside a handle rect
        nearby = self.preview_canvas.find_overlapping(x, y, x, y)
        for item in nearby:
            tags = self.preview_canvas.gettags(item)
            for t in tags:
                if t.startswith('handle_'):
                    return t.split('_', 1)[1]
        return None

    def _point_in_roi_norm(self, xn, yn):
        if self._roi_norm is None:
            return False
        x0, y0, x1, y1 = self._roi_norm
        return x0 <= xn <= x1 and y0 <= yn <= y1

    def _point_in_roi_canvas(self, x, y):
        # Convert canvas point to full image norm and reuse
        cw = int(self.preview_canvas.cget('width'))
        ch = int(self.preview_canvas.cget('height'))
        if self._view_window_norm is not None:
            vx0, vy0, vx1, vy1 = self._view_window_norm
        else:
            vx0, vy0, vx1, vy1 = (0.0, 0.0, 1.0, 1.0)
        xn = vx0 + (x / cw) * (vx1 - vx0)
        yn = vy0 + (y / ch) * (vy1 - vy0)
        return self._point_in_roi_norm(xn, yn)

    def _clear_roi(self):
        self._roi_norm = None
        self.update_preview()

    def select_best_color(self):
        """Automatically select the best color for ambient lighting"""
        dominant_colors = self.color_logic.get_dominant_colors(
            10
        )  # Get more colors to analyze

        if not dominant_colors:
            self.prevalence_var.set(
                "❌ No colorful accent colors found - screen contains only grays/blacks"
            )
            self.analysis_var.set(
                "The screen contains mostly grayscale content (blacks, grays, whites) which are not suitable for ambient lighting. Try a different screen content with more colors."
            )
            return

        best_color = self.color_logic.get_best_ambient_color(dominant_colors)

        if best_color:
            # Select the best color
            self.color_logic.update_selection(
                best_color, self.color_logic.selected_position
            )
            self.update_color_info()
            self.update_preview()

            # Update selection indicator
            width = self.color_map_canvas.winfo_width() or 400
            height = self.color_map_canvas.winfo_height() or 300

            try:
                r = int(best_color[1:3], 16) / 255
                g = int(best_color[3:5], 16) / 255
                b = int(best_color[5:7], 16) / 255

                import colorsys

                h, s, v = colorsys.rgb_to_hsv(r, g, b)

                x = int(h * width)
                y = int((1 - v * 0.5) * height)

                self.update_selection_indicator(x, y)
            except Exception:
                self.update_selection_indicator(width // 2, height // 2)

            # Find the percentage of this color
            color_percentage = next(
                (p for c, p in dominant_colors if c == best_color), 0
            )

            self.prevalence_var.set(
                f"🎯 Auto-selected best color: {best_color} ({color_percentage:.1f}% of screen)"
            )
            self.analysis_var.set(
                f"Smart selection chose this color as the best for ambient lighting. It has good saturation, appropriate brightness, and avoids grayscale tones."
            )

        else:
            self.prevalence_var.set(
                "❌ No suitable colors found - only low-quality colors available"
            )
            self.analysis_var.set(
                "While some colors were found, none meet the quality criteria for good ambient lighting (sufficient saturation, appropriate brightness, etc.)."
            )

    def update_dominant_colors(self):
        """Update dominant colors display"""
        # Clear existing
        for widget in self.dominant_colors_frame.winfo_children():
            widget.destroy()

        # Compute dominant colors possibly within ROI by temporarily cropping the thumbnail
        dominant_colors = None
        try:
            img = self.color_logic.screen_thumbnail
            if img and self._roi_norm is not None:
                from PIL import Image
                w, h = img.size
                x0 = int(self._roi_norm[0] * w)
                y0 = int(self._roi_norm[1] * h)
                x1 = int(self._roi_norm[2] * w)
                y1 = int(self._roi_norm[3] * h)
                # Ensure minimum size
                if x1 - x0 >= 2 and y1 - y0 >= 2:
                    orig = img
                    cropped = img.crop((x0, y0, x1, y1))
                    self.color_logic.screen_thumbnail = cropped
                    dominant_colors = self.color_logic.get_dominant_colors(8)
                    # Restore
                    self.color_logic.screen_thumbnail = orig
            if dominant_colors is None:
                dominant_colors = self.color_logic.get_dominant_colors(8)
        except Exception:
            dominant_colors = self.color_logic.get_dominant_colors(8)

        if dominant_colors:
            # Create a grid layout for dominant colors
            for i, (color, percentage) in enumerate(dominant_colors):
                row = i // 2
                col = i % 2

                color_frame = ttk.Frame(self.dominant_colors_frame)
                color_frame.grid(row=row, column=col, padx=2, pady=2, sticky=tk.W)

                # Color button
                color_btn = tk.Button(
                    color_frame,
                    text="",
                    bg=color,
                    width=3,
                    height=1,
                    relief="raised",
                    bd=2,
                    command=lambda c=color: self.select_dominant_color(c),
                )
                color_btn.pack(side=tk.LEFT, padx=(0, 3))

                # Percentage
                ttk.Label(
                    color_frame, text=f"{percentage:.1f}%", font=("Segoe UI", 7)
                ).pack(side=tk.LEFT)
        else:
            ttk.Label(
                self.dominant_colors_frame,
                text="No colorful accent colors found\n(Only grays/blacks detected)",
                font=("Segoe UI", 8),
                foreground="#666666",
                justify=tk.CENTER,
            ).pack()

    def select_dominant_color(self, color: str):
        """Select a dominant color"""
        self.color_logic.update_selection(color, self.color_logic.selected_position)
        self.update_color_info()
        self.update_preview()

        # Update selection indicator - find approximate position for this color
        width = self.color_map_canvas.winfo_width() or 400
        height = self.color_map_canvas.winfo_height() or 300

        # Convert color back to approximate position
        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255

            import colorsys

            h, s, v = colorsys.rgb_to_hsv(r, g, b)

            # Map back to canvas coordinates
            x = int(h * width)
            y = int((1 - v * 0.5) * height)

            self.update_selection_indicator(x, y)
        except Exception:
            # If conversion fails, just center the indicator
            self.update_selection_indicator(width // 2, height // 2)

    def populate_monitor_list(self):
        """Populate monitor dropdown"""
        monitors = ["Monitor 1"]

        try:
            if SCREEN_CAPTURE_AVAILABLE:
                import mss

                with mss.mss() as sct:
                    monitor_names = []
                    for i, monitor in enumerate(sct.monitors):
                        if i == 0:
                            continue
                        monitor_names.append(
                            f"Monitor {i} ({monitor['width']}x{monitor['height']})"
                        )

                    if monitor_names:
                        monitors = monitor_names
        except Exception:
            pass

        self.monitor_combo["values"] = monitors
        if monitors:
            self.monitor_combo.current(0)

    def on_monitor_change(self, event=None):
        """Handle monitor selection change"""
        try:
            selected_idx = self.monitor_combo.current()
            self.color_logic.monitor_index = selected_idx + 1
            self.refresh_screen_preview()
        except Exception:
            pass

    def start_auto_refresh(self):
        """Start auto-refresh"""
        if self.auto_refresh_var.get():
            self.refresh_screen_preview()
            self.refresh_timer = self.window.after(1000, self.start_auto_refresh)

    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        if self.refresh_timer:
            self.window.after_cancel(self.refresh_timer)
            self.refresh_timer = None

        if self.auto_refresh_var.get():
            self.start_auto_refresh()

    def refresh_screen_preview(self):
        """Refresh screen preview"""
        try:
            self.color_logic.capture_screen_thumbnail()
            self.update_preview()
        except Exception:
            pass

    def choose_custom_color(self):
        """Choose custom color"""
        color = colorchooser.askcolor(
            title="Choose Custom Color", initialcolor=self.color_logic.selected_color
        )
        if color and color[1]:
            self.color_logic.update_selection(
                color[1], self.color_logic.selected_position
            )
            self.update_color_info()
            self.update_preview()

            # Update selection indicator - find approximate position
            width = self.color_map_canvas.winfo_width() or 400
            height = self.color_map_canvas.winfo_height() or 300

            try:
                r = int(color[1][1:3], 16) / 255
                g = int(color[1][3:5], 16) / 255
                b = int(color[1][5:7], 16) / 255

                import colorsys

                h, s, v = colorsys.rgb_to_hsv(r, g, b)

                x = int(h * width)
                y = int((1 - v * 0.5) * height)

                self.update_selection_indicator(x, y)
            except Exception:
                self.update_selection_indicator(width // 2, height // 2)

    def reset_selection(self):
        """Reset to center"""
        width = self.color_map_canvas.winfo_width() or 400
        height = self.color_map_canvas.winfo_height() or 300
        self.update_selection_from_click(width // 2, height // 2)

    def sample_screen_color(self):
        """Sample color from screen"""
        try:
            position = self.color_logic.selected_position
            sampled_color = self.color_logic.get_color_at_screen_position(
                position, self.color_logic.monitor_index
            )

            if sampled_color:
                self.color_logic.update_selection(sampled_color, position)
                self.update_color_info()
                self.update_preview()

                # Update selection indicator
                width = self.color_map_canvas.winfo_width() or 400
                height = self.color_map_canvas.winfo_height() or 300

                try:
                    r = int(sampled_color[1:3], 16) / 255
                    g = int(sampled_color[3:5], 16) / 255
                    b = int(sampled_color[5:7], 16) / 255

                    import colorsys

                    h, s, v = colorsys.rgb_to_hsv(r, g, b)

                    x = int(h * width)
                    y = int((1 - v * 0.5) * height)

                    self.update_selection_indicator(x, y)
                except Exception:
                    self.update_selection_indicator(width // 2, height // 2)

                self.status_var.set(f"Sampled screen color: {sampled_color}")
            else:
                self.status_var.set("Could not sample screen color")
        except Exception as e:
            self.status_var.set(f"Sampling error: {str(e)}")

    def apply_color(self):
        """Apply selected color to lamp"""
        if not self.device_manager.is_connected:
            self.status_var.set("❌ Not connected to lamp!")
            return

        color = self.color_logic.selected_color

        try:
            # Stop any running effects
            self.effects_engine.stop_all_effects()

            # Apply color
            self.effects_engine.set_color_from_hex(color, 1.0)

            self.status_var.set(f"✅ Applied {color} to lamp")
            self.log_event("OUT", color, "Manual apply to lamp")

        except Exception as e:
            self.status_var.set(f"❌ Error applying color: {str(e)}")

    def toggle_live_mode(self):
        """Toggle live mode for smart ambient lighting"""
        if self.live_var.get():
            # Start live mode
            self.start_live_mode()
        else:
            # Stop live mode
            self.stop_live_mode()

    def start_live_mode(self):
        """Start live mode using smart ambient processor"""
        if not self.device_manager.is_connected:
            self.status_var.set("❌ Connect lamp first to use Live mode!")
            self.live_var.set(False)
            return

        self.live_mode = True

        # Set monitor to match current selection
        selected_idx = self.monitor_combo.current()
        self.smart_ambient.set_monitor(selected_idx + 1)

        # Start the smart ambient processor
        success = self.smart_ambient.start(
            color_callback=self.on_live_color_update,
            status_callback=self.on_live_status_update,
        )

        if success:
            # Prepare lamp for live color updates
            try:
                self.effects_engine.stop_all_effects()
                if hasattr(self.device_manager, "set_mode"):
                    self.device_manager.set_mode("colour")
            except Exception:
                pass
            self.status_var.set("🔴 Live mode active - using screen accent colors")
            # Disable manual controls during live mode
            self.best_color_btn.config(state="disabled")
        else:
            self.live_mode = False
            self.live_var.set(False)
            self.status_var.set("❌ Failed to start Live mode")

    def stop_live_mode(self):
        """Stop live mode"""
        if self.smart_ambient.is_running():
            self.smart_ambient.stop()

        self.live_mode = False
        self.status_var.set("Live mode stopped")

        # Re-enable manual controls
        self.best_color_btn.config(state="normal")
        
       
    def log_event(self, direction, color, message):
        import time
        ts = time.strftime("%H:%M:%S")
        color_norm = (color or "").strip().lower()
        try:
            print(f"[{ts}] {direction:<3} {color_norm:<8} {message}")
        except Exception:
            pass
        # Add to global history; UI updates via subscription
        try:
            HIST.add(direction, color, message)
        except Exception:
            pass

    def _on_history_update(self, entries):
        # Render global history into the local Text widget with color swatches
        if not hasattr(self, "history_text"):
            return
        try:
            self.history_text.configure(state=tk.NORMAL)
            self.history_text.delete("1.0", tk.END)
            for ts_i, dir_i, col_i, msg_i in entries:
                # Optional color swatch
                if col_i and isinstance(col_i, str) and col_i.startswith('#') and len(col_i) == 7:
                    tag = f"swatch_{col_i}"
                    if tag not in self.history_text.tag_names():
                        try:
                            r = int(col_i[1:3], 16)
                            g = int(col_i[3:5], 16)
                            b = int(col_i[5:7], 16)
                            luminance = 0.2126*r + 0.7152*g + 0.0722*b
                            fg = '#000000' if luminance > 160 else '#ffffff'
                            self.history_text.tag_configure(tag, background=col_i, foreground=fg)
                        except Exception:
                            tag = None
                    if tag in self.history_text.tag_names():
                        self.history_text.insert(tk.END, '   ', tag)
                        self.history_text.insert(tk.END, ' ')
                line_txt = f"[{ts_i}] {dir_i:<3} {col_i:<8} {msg_i}"
                self.history_text.insert(tk.END, line_txt + "\n")
            self.history_text.see(tk.END)
            self.history_text.configure(state=tk.DISABLED)
        except Exception:
            pass

        # Update the 5-second rolling history
        if not hasattr(self, "recent_text"):
            return
        try:
            now = time.time()
            cutoff = now - 5.0
            # Filter entries within the last 5 seconds
            recent_entries = []
            for ts_i, dir_i, col_i, msg_i in entries:
                try:
                    # Parse HH:MM:SS into seconds since midnight
                    h, m, s = map(int, ts_i.split(':'))
                    secs_since_midnight = h*3600 + m*60 + s
                    # Get current seconds since midnight
                    now_h, now_m, now_s = map(int, time.strftime('%H:%M:%S').split(':'))
                    now_secs = now_h*3600 + now_m*60 + now_s
                    # Handle wrap-around at midnight
                    entry_time = secs_since_midnight
                    if now_secs >= entry_time:
                        delta = now_secs - entry_time
                    else:
                        delta = (24*3600 - entry_time) + now_secs
                    if delta <= 5:
                        recent_entries.append((ts_i, dir_i, col_i, msg_i))
                except Exception:
                    # Include entry if parsing fails
                    recent_entries.append((ts_i, dir_i, col_i, msg_i))
            # Render recent entries
            self.recent_text.configure(state=tk.NORMAL)
            self.recent_text.delete("1.0", tk.END)
            for ts_i, dir_i, col_i, msg_i in recent_entries:
                if col_i and isinstance(col_i, str) and col_i.startswith('#') and len(col_i) == 7:
                    tag = f"recent_swatch_{col_i}"
                    if tag not in self.recent_text.tag_names():
                        try:
                            r = int(col_i[1:3], 16)
                            g = int(col_i[3:5], 16)
                            b = int(col_i[5:7], 16)
                            luminance = 0.2126*r + 0.7152*g + 0.0722*b
                            fg = '#000000' if luminance > 160 else '#ffffff'
                            self.recent_text.tag_configure(tag, background=col_i, foreground=fg)
                        except Exception:
                            tag = None
                    if tag in self.recent_text.tag_names():
                        self.recent_text.insert(tk.END, '   ', tag)
                        self.recent_text.insert(tk.END, ' ')
                line_txt = f"[{ts_i}] {dir_i:<3} {col_i:<8} {msg_i}"
                self.recent_text.insert(tk.END, line_txt + "\n")
            self.recent_text.see(tk.END)
            self.recent_text.configure(state=tk.DISABLED)
        except Exception:
            pass


    def on_live_color_update(self, color: str):
        # Always bounce to Tk main thread
        self.window.after(0, self._handle_live_color_ui, color)


    def _handle_live_color_ui(self, color: str):
        # Send live update to lamp and log
        try:
            # Ensure lamp is in colour mode; avoid heavy operations each tick
            if hasattr(self.device_manager, "set_mode"):
                self.device_manager.set_mode("colour")
            self.effects_engine.set_color_from_hex(color, 1.0)
            self.log_event("OUT", color, "Live color pulse sent to lamp")
        except Exception as e:
            self.log_event("ERR", color, f"Live update failed: {e}")

        self.color_logic.update_selection(
            color, self.color_logic.selected_position
        )

        self.update_color_info()
        self.update_selection_indicator_from_color(color)
        self.status_var.set(f"Live: {color}")

    def _update_sim_canvas(self, color_hex: str):
        try:
            self.sim_canvas.itemconfig(self.sim_bulb, fill=color_hex)
            # Adjust outline for contrast
            self.sim_canvas.itemconfig(self.sim_bulb, outline=color_hex)
        except Exception:
            pass

    def on_live_status_update(self, status: str):
        self.window.after(0, self._handle_live_status_ui, status)


    def _handle_live_status_ui(self, status: str):
        self.log_event("IN", "", f"Live status: {status}")
        self.status_var.set(status)

    def update_selection_indicator_from_color(self, color: str):
        """Update selection indicator based on color"""
        width = self.color_map_canvas.winfo_width() or 400
        height = self.color_map_canvas.winfo_height() or 300

        try:
            r = int(color[1:3], 16) / 255
            g = int(color[3:5], 16) / 255
            b = int(color[5:7], 16) / 255

            import colorsys

            h, s, v = colorsys.rgb_to_hsv(r, g, b)

            x = int(h * width)
            y = int((1 - v * 0.5) * height)

            self.update_selection_indicator(x, y)
        except Exception:
            self.update_selection_indicator(width // 2, height // 2)

    def on_close(self):
        """Handle window close"""
        # Stop live mode
        if self.live_mode:
            self.stop_live_mode()

        if self.refresh_timer:
            self.window.after_cancel(self.refresh_timer)
        self.window.destroy()


def open_color_map_window(parent, device_manager, effects_engine):
    """Open the color map window"""
    return ColorMapWindow(parent, device_manager, effects_engine)
