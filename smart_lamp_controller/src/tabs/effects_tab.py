#!/usr/bin/env python3
"""
Effects Tab - Rainbow, blinker, strobe, and other visual effects
"""

import tkinter as tk
from tkinter import ttk
import colorsys
from .base_tab import BaseTab


class EffectsTab(BaseTab):
    """Tab for visual effects control"""

    def get_tab_title(self) -> str:
        return "Effects"

    def _build_content(self):
        self._setup_rainbow_effect()
        self._setup_blinker_effect()
        self._setup_strobe_effect()
        self._setup_white_strobe_effect()
        self._setup_tuya_scenes()

    def _setup_rainbow_effect(self):
        """Setup rainbow effect controls"""
        rainbow_frame = self.create_labeled_frame("Rainbow Effect")

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
        ttk.Scale(
            range_frame,
            from_=0.0,
            to=1.0,
            variable=self.rainbow_h_min,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_rainbow_preview()
        ).pack(fill=tk.X, pady=(0, 5))

        ttk.Label(range_frame, text="Color Range - End Hue").pack(anchor=tk.W)
        self.rainbow_h_max = tk.DoubleVar(value=1.0)
        ttk.Scale(
            range_frame,
            from_=0.0,
            to=1.0,
            variable=self.rainbow_h_max,
            orient=tk.HORIZONTAL,
            command=lambda x: self.update_rainbow_preview()
        ).pack(fill=tk.X)

        # Rainbow control button
        self.rainbow_btn = ttk.Button(
            rainbow_frame,
            text="Start Rainbow",
            command=self.toggle_rainbow
        )
        self.rainbow_btn.pack(fill=tk.X, pady=(10, 0))

        # Initialize preview
        self.root.after(100, self.update_rainbow_preview)

        # Export to controller
        self.controller.rainbow_btn = self.rainbow_btn
        self.controller.rainbow_speed_var = self.rainbow_speed_var
        self.controller.rainbow_h_min = self.rainbow_h_min
        self.controller.rainbow_h_max = self.rainbow_h_max

    def _setup_blinker_effect(self):
        """Setup blinker effect controls"""
        blinker_frame = self.create_labeled_frame("Blinker / Party Mode")

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
            text="Start Blinker",
            command=self.toggle_blinker
        )
        self.blinker_btn.pack(fill=tk.X)

        # Export to controller
        self.controller.blinker_btn = self.blinker_btn
        self.controller.blinker_speed_var = self.blinker_speed_var

    def _setup_strobe_effect(self):
        """Setup strobe effect controls"""
        strobe_frame = self.create_labeled_frame("Strobe / Party On-Off")

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
            text="Start Strobe",
            command=self.toggle_strobe
        )
        self.strobe_btn.pack(fill=tk.X)

        # Export to controller
        self.controller.strobe_btn = self.strobe_btn
        self.controller.strobe_speed_var = self.strobe_speed_var

    def _setup_white_strobe_effect(self):
        """Setup white strobe effect controls"""
        white_strobe_frame = self.create_labeled_frame("White Strobe / Party Flash")

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
            text="Start White Strobe",
            command=self.toggle_white_strobe
        )
        self.white_strobe_btn.pack(fill=tk.X)

        # Export to controller
        self.controller.white_strobe_btn = self.white_strobe_btn
        self.controller.white_strobe_speed_var = self.white_strobe_speed_var

    def _setup_tuya_scenes(self):
        """Setup built-in Tuya scenes"""
        scenes_frame = self.create_labeled_frame("Built-in Scenes (Tuya)")

        ttk.Label(
            scenes_frame,
            text="Select a hardware scene:",
            font=("Segoe UI", 8, "italic")
        ).pack(anchor=tk.W, pady=(0, 10))

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

    # Event handlers
    def update_rainbow_preview(self):
        """Update rainbow effect preview"""
        if not hasattr(self, 'rainbow_canvas'):
            return

        self.rainbow_canvas.delete("all")

        h_min = self.rainbow_h_min.get()
        h_max = self.rainbow_h_max.get()
        width = self.rainbow_canvas.winfo_width() or 400

        for x in range(width):
            hue = h_min + (h_max - h_min) * (x / width)
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
            self.rainbow_canvas.create_line(x, 0, x, 40, fill=color)

    def toggle_rainbow(self):
        """Toggle rainbow effect"""
        if not self.check_connection():
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
            self.controller._reset_effect_buttons('rainbow')

    def toggle_blinker(self):
        """Toggle blinker effect"""
        if not self.check_connection():
            return

        if self.effects_engine.blinker_running:
            self.effects_engine.stop_blinker_effect()
            self.blinker_btn.config(text="Start Blinker")
        else:
            self.effects_engine.set_blinker_parameters(
                speed=self.blinker_speed_var.get()
            )
            self.effects_engine.start_blinker_effect()
            self.blinker_btn.config(text="Stop Blinker")
            self.controller._reset_effect_buttons('blinker')

    def update_blinker_parameters(self):
        """Update blinker parameters live"""
        if self.effects_engine.blinker_running:
            self.effects_engine.set_blinker_parameters(
                speed=self.blinker_speed_var.get()
            )

    def toggle_strobe(self):
        """Toggle strobe effect"""
        if not self.check_connection():
            return

        if self.effects_engine.strobe_running:
            self.effects_engine.stop_strobe_effect()
            self.strobe_btn.config(text="Start Strobe")
        else:
            self.effects_engine.set_strobe_parameters(
                speed=self.strobe_speed_var.get()
            )
            self.effects_engine.start_strobe_effect()
            self.strobe_btn.config(text="Stop Strobe")
            self.controller._reset_effect_buttons('strobe')

    def update_strobe_parameters(self):
        """Update strobe parameters live"""
        if self.effects_engine.strobe_running:
            self.effects_engine.set_strobe_parameters(
                speed=self.strobe_speed_var.get()
            )

    def toggle_white_strobe(self):
        """Toggle white strobe effect"""
        if not self.check_connection():
            return

        if self.effects_engine.white_strobe_running:
            self.effects_engine.stop_white_strobe_effect()
            self.white_strobe_btn.config(text="Start White Strobe")
        else:
            self.effects_engine.set_white_strobe_parameters(
                speed=self.white_strobe_speed_var.get()
            )
            self.effects_engine.start_white_strobe_effect()
            self.white_strobe_btn.config(text="Stop White Strobe")
            self.controller._reset_effect_buttons('white_strobe')

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
        self.controller._reset_effect_buttons()
        if hasattr(self.controller, 'mode_var'):
            self.controller.mode_var.set("scene")
