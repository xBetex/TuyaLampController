#!/usr/bin/env python3
"""
Ambilight Tab - Screen synchronization and smart ambient controls
"""

import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab

# Check if ambilight dependencies are available
try:
    from core.ambilight_processor import AMBILIGHT_AVAILABLE
except ImportError:
    AMBILIGHT_AVAILABLE = False


class AmbilightTab(BaseTab):
    """Tab for screen sync and smart ambient lighting"""

    def get_tab_title(self) -> str:
        return "Screen Sync"

    def _build_content(self):
        self._setup_screen_sync()
        self._setup_smart_ambient()
        self._setup_tech_info()

    def _setup_screen_sync(self):
        """Setup screen sync (Ambilight) controls"""
        # Header
        ttk.Label(
            self.content,
            text="Ambilight / Screen Sync",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            self.content,
            text="Synchronizes the lamp with your main monitor's dominant color.",
            wraplength=400
        ).pack(pady=(0, 20))

        # Controls Frame
        ctrl_frame = self.create_labeled_frame("Settings")

        # Alpha/Smoothing
        ttk.Label(ctrl_frame, text="Smoothing (Response speed):").pack(anchor=tk.W)
        self.ambi_alpha_var = tk.DoubleVar(value=0.2)
        ttk.Scale(
            ctrl_frame,
            from_=0.05,
            to=0.6,
            variable=self.ambi_alpha_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.on_ambilight_smoothing_change()
        ).pack(fill=tk.X, pady=(5, 5))

        ttk.Label(
            ctrl_frame,
            text="Slow / Smooth <---> Fast / Reactive",
            font=("Segoe UI", 7, "italic")
        ).pack(fill=tk.X, pady=(0, 15))

        # Edge Cropping
        ttk.Label(ctrl_frame, text="Edge Crop % (Ignore Taskbar/Headers):").pack(anchor=tk.W)
        self.ambi_crop_var = tk.IntVar(value=15)
        ttk.Scale(
            ctrl_frame,
            from_=0,
            to=35,
            variable=self.ambi_crop_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.on_ambilight_crop_change()
        ).pack(fill=tk.X, pady=(5, 5))

        ttk.Label(
            ctrl_frame,
            text="Full Screen <---> Center Only",
            font=("Segoe UI", 7, "italic")
        ).pack(fill=tk.X, pady=(0, 15))

        # Monitor selection
        ttk.Label(ctrl_frame, text="Select Display:").pack(anchor=tk.W)
        self.ambi_monitor_var = tk.StringVar()
        self.monitor_combo = ttk.Combobox(
            ctrl_frame,
            textvariable=self.ambi_monitor_var,
            state="readonly"
        )
        self._populate_monitors()
        self.monitor_combo.pack(fill=tk.X, pady=(5, 10))
        self.monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.on_ambilight_monitor_change())

        # Start/Stop Button
        self.ambi_btn = ttk.Button(
            self.content,
            text="Start Screen Sync",
            command=self.toggle_ambilight
        )
        self.ambi_btn.pack(fill=tk.X, ipady=10)

        ttk.Separator(self.content, orient='horizontal').pack(fill=tk.X, pady=20)

        # Export to controller
        self.controller.ambi_btn = self.ambi_btn
        self.controller.ambi_alpha_var = self.ambi_alpha_var
        self.controller.ambi_crop_var = self.ambi_crop_var
        self.controller.monitor_combo = self.monitor_combo

    def _setup_smart_ambient(self):
        """Setup smart ambient lighting controls"""
        ttk.Label(
            self.content,
            text="Smart Ambient Lighting",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            self.content,
            text="Automatically selects the best accent colors from your screen for ambient lighting.",
            wraplength=400
        ).pack(pady=(0, 20))

        # Smart Ambient Controls
        smart_ctrl_frame = self.create_labeled_frame("Smart Ambient Settings")

        # Update interval
        ttk.Label(smart_ctrl_frame, text="Update Interval (seconds):").pack(anchor=tk.W)
        self.smart_interval_var = tk.DoubleVar(value=1.0)
        ttk.Scale(
            smart_ctrl_frame,
            from_=0.5,
            to=5.0,
            variable=self.smart_interval_var,
            orient=tk.HORIZONTAL,
            command=lambda x: self.on_smart_interval_change()
        ).pack(fill=tk.X, pady=(5, 5))

        ttk.Label(
            smart_ctrl_frame,
            text="Fast (0.5s) <---> Slow (5s)",
            font=("Segoe UI", 7, "italic")
        ).pack(fill=tk.X, pady=(0, 15))

        # Monitor selection for smart ambient
        ttk.Label(smart_ctrl_frame, text="Monitor for Analysis:").pack(anchor=tk.W)
        self.smart_monitor_var = tk.StringVar()
        self.smart_monitor_combo = ttk.Combobox(
            smart_ctrl_frame,
            textvariable=self.smart_monitor_var,
            state="readonly"
        )
        self.smart_monitor_combo['values'] = self.monitor_combo['values']
        if self.smart_monitor_combo['values']:
            self.smart_monitor_combo.current(0)
        self.smart_monitor_combo.pack(fill=tk.X, pady=(5, 10))
        self.smart_monitor_combo.bind("<<ComboboxSelected>>", lambda e: self.on_smart_monitor_change())

        # Status display
        self.smart_status_var = tk.StringVar(value="Smart ambient lighting stopped")
        ttk.Label(
            smart_ctrl_frame,
            textvariable=self.smart_status_var,
            font=("Segoe UI", 9),
            foreground="#666666"
        ).pack(anchor=tk.W, pady=(10, 0))

        # Start/Stop Button for Smart Ambient
        self.smart_ambi_btn = ttk.Button(
            self.content,
            text="Start Smart Ambient",
            command=self.toggle_smart_ambient
        )
        self.smart_ambi_btn.pack(fill=tk.X, ipady=10)

        # Export to controller
        self.controller.smart_ambi_btn = self.smart_ambi_btn
        self.controller.smart_status_var = self.smart_status_var
        self.controller.smart_interval_var = self.smart_interval_var
        self.controller.smart_monitor_combo = self.smart_monitor_combo

    def _setup_tech_info(self):
        """Setup tech info footer"""
        tech_frame = ttk.Frame(self.content)
        tech_frame.pack(fill=tk.X, pady=(30, 0))

        ttk.Label(
            tech_frame,
            text="Tech: HSV-Weighted dominant color extraction with temporal smoothing.",
            font=("Segoe UI", 8, "italic"),
            foreground="gray"
        ).pack()

        ttk.Label(
            tech_frame,
            text="Smart Ambient: Intelligent color scoring with grayscale filtering.",
            font=("Segoe UI", 8, "italic"),
            foreground="gray"
        ).pack()

    def _populate_monitors(self):
        """Populate monitor selection dropdown"""
        monitors = []

        if AMBILIGHT_AVAILABLE:
            try:
                import mss
                with mss.mss() as sct:
                    for i, m in enumerate(sct.monitors):
                        if i == 0:
                            continue  # Skip 'all monitors' virtual display
                        monitors.append(f"Display {i} ({m['width']}x{m['height']})")
            except Exception:
                pass

        if not monitors:
            monitors = ["Primary Display"]

        self.monitor_combo['values'] = monitors
        if monitors:
            self.monitor_combo.current(0)

    # Event handlers
    def toggle_ambilight(self):
        """Toggle screen sync (Ambilight) effect"""
        if not self.check_connection():
            return

        if not AMBILIGHT_AVAILABLE:
            self.show_error(
                "Ambilight Error",
                "Ambilight dependencies (mss, cv2) not available"
            )
            return

        if self.effects_engine.ambilight_running:
            self.effects_engine.stop_ambilight_effect()
            self.ambi_btn.config(text="Start Screen Sync")
        else:
            self.effects_engine.set_ambilight_parameters(
                alpha=self.ambi_alpha_var.get(),
                monitor_index=self.monitor_combo.current() + 1,
                crop_percent=self.ambi_crop_var.get()
            )
            self.effects_engine.start_ambilight_effect()
            self.ambi_btn.config(text="Stop Screen Sync")
            self.controller._reset_effect_buttons('ambi')

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

    def toggle_smart_ambient(self):
        """Toggle Smart Ambient effect"""
        if not self.check_connection():
            return

        if self.effects_engine.smart_ambient_running:
            self.effects_engine.stop_smart_ambient_effect()
            self.smart_ambi_btn.config(text="Start Smart Ambient")
            self.smart_status_var.set("Smart ambient lighting stopped")
        else:
            self.effects_engine.set_smart_ambient_parameters(
                monitor_index=self.smart_monitor_combo.current() + 1,
                update_interval=self.smart_interval_var.get()
            )

            success = self.effects_engine.start_smart_ambient_effect()
            if success:
                self.smart_ambi_btn.config(text="Stop Smart Ambient")
                self.controller._reset_effect_buttons('smart_ambient')
            else:
                self.show_error(
                    "Smart Ambient Error",
                    "Failed to start smart ambient lighting. Check that screen capture dependencies are installed."
                )

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
