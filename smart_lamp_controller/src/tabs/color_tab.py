#!/usr/bin/env python3
"""
Color Tab - Static color selection and color picker
"""

import tkinter as tk
from tkinter import ttk, colorchooser
from .base_tab import BaseTab


class ColorTab(BaseTab):
    """Tab for static color control and color picker"""

    def get_tab_title(self) -> str:
        return "Static Color"

    def _build_content(self):
        # Color intensity control
        intensity_frame = self.create_labeled_frame("Color Intensity")

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

        # Color picker section
        picker_frame = self.create_labeled_frame("Color Selection")

        ttk.Button(
            picker_frame,
            text="Choose Color",
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

        # Quick color buttons
        colors_frame = self.create_labeled_frame("Quick Colors")

        color_grid = ttk.Frame(colors_frame)
        color_grid.pack(fill=tk.X)

        quick_colors = [
            ("#ff0000", "Red"),
            ("#00ff00", "Green"),
            ("#0000ff", "Blue"),
            ("#ffff00", "Yellow"),
            ("#00ffff", "Cyan"),
            ("#ff00ff", "Magenta"),
            ("#ff8000", "Orange"),
            ("#8000ff", "Purple"),
        ]

        for i, (color, name) in enumerate(quick_colors):
            btn = tk.Button(
                color_grid,
                text="",
                bg=color,
                width=4,
                height=2,
                relief="raised",
                command=lambda c=color: self.apply_quick_color(c)
            )
            row, col = divmod(i, 4)
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            color_grid.columnconfigure(col, weight=1)

        # Color Map launcher
        map_frame = self.create_labeled_frame("Advanced")

        ttk.Label(
            map_frame,
            text="Open the color map for advanced selection with screen analysis",
            font=("Segoe UI", 9),
            foreground="#666666"
        ).pack(anchor=tk.W, pady=(0, 10))

        ttk.Button(
            map_frame,
            text="Open Color Map Window",
            command=self.open_color_map_window
        ).pack(fill=tk.X)

        # Export variables to controller for compatibility
        self.controller.color_bright_var = self.color_bright_var
        self.controller.color_preview = self.color_preview

    def on_color_brightness_change(self, event):
        """Handle color brightness change"""
        import colorsys

        # Update effects engine stored brightness
        self.effects_engine.color_brightness = self.color_bright_var.get()

        # If we're on static color, apply brightness immediately
        try:
            v = float(self.color_bright_var.get()) / 1000.0
        except Exception:
            v = 1.0

        if hasattr(self.effects_engine, 'last_hsv') and self.effects_engine.last_hsv:
            h, s, _ = self.effects_engine.last_hsv
            r, g, b = colorsys.hsv_to_rgb(h, s, max(0.0, min(1.0, v)))
            self.device_manager.set_color(r*255, g*255, b*255)
            hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
            self.color_preview.config(bg=hex_color)

    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose Lamp Color")
        if color and color[1]:
            self.apply_color(color[1])

    def apply_quick_color(self, hex_color: str):
        """Apply a quick color preset"""
        self.apply_color(hex_color)

    def apply_color(self, hex_color: str):
        """Apply a color to the lamp"""
        self.effects_engine.set_color_from_hex(
            hex_color,
            self.color_bright_var.get() / 1000.0
        )
        self.color_preview.config(bg=hex_color)

        # Set mode to color
        if hasattr(self.controller, 'mode_var'):
            self.controller.mode_var.set("colour")
        self.device_manager.set_mode("colour")

    def open_color_map_window(self):
        """Open the color map window"""
        try:
            from color_map_window import open_color_map_window
            open_color_map_window(self.root, self.device_manager, self.effects_engine)
        except Exception as e:
            self.show_error(
                "Error",
                f"Failed to open color map window:\n{str(e)}"
            )
