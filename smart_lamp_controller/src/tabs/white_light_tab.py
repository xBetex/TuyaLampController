#!/usr/bin/env python3
"""
White Light Tab - Brightness and color temperature controls
"""

import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab


class WhiteLightTab(BaseTab):
    """Tab for white light brightness and temperature control"""

    def get_tab_title(self) -> str:
        return "White Light"

    def _build_content(self):
        # Brightness control
        bright_frame = self.create_labeled_frame("Brightness")

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
        temp_frame = self.create_labeled_frame("Color Temperature")

        ttk.Label(temp_frame, text="Temperature (Warm <-> Cool)").pack(anchor=tk.W)

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

        # Quick presets
        presets_frame = self.create_labeled_frame("Quick Presets")

        preset_grid = ttk.Frame(presets_frame)
        preset_grid.pack(fill=tk.X)

        presets = [
            ("Warm", 200, 700),
            ("Neutral", 500, 500),
            ("Cool", 800, 500),
            ("Dim", 500, 100),
            ("Bright", 500, 900),
            ("Reading", 400, 700),
        ]

        for i, (name, temp, bright) in enumerate(presets):
            btn = ttk.Button(
                preset_grid,
                text=name,
                command=lambda t=temp, b=bright: self.apply_preset(t, b)
            )
            row, col = divmod(i, 3)
            btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            preset_grid.columnconfigure(col, weight=1)

        # Export variables to controller for compatibility
        self.controller.brightness_var = self.brightness_var
        self.controller.temp_var = self.temp_var

    def on_brightness_change(self, event):
        """Handle brightness change"""
        self.device_manager.set_brightness(int(self.brightness_var.get()))

    def on_temp_change(self, event):
        """Handle temperature change"""
        self.device_manager.set_temperature(int(self.temp_var.get()))

    def apply_preset(self, temp: int, bright: int):
        """Apply a quick preset"""
        self.temp_var.set(temp)
        self.brightness_var.set(bright)
        self.device_manager.set_temperature(temp)
        self.device_manager.set_brightness(bright)
