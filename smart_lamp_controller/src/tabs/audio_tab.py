#!/usr/bin/env python3
"""
Audio Tab - Music synchronization controls
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
from .base_tab import BaseTab

# Check audio availability
try:
    from core.audio_processor import AUDIO_AVAILABLE
except ImportError:
    AUDIO_AVAILABLE = False


class AudioTab(BaseTab):
    """Tab for music sync / audio reactive effects"""

    def get_tab_title(self) -> str:
        return "Music Sync"

    def _build_content(self):
        if not AUDIO_AVAILABLE:
            ttk.Label(
                self.content,
                text="Audio features not available.\n\nInstall pyaudio, numpy, scipy for music sync.",
                font=("Segoe UI", 11),
                foreground="#666666"
            ).pack(expand=True)
            return

        self._setup_audio_mode()
        self._setup_visualization()
        self._setup_device_selection()
        self._setup_sync_controls()

    def _setup_audio_mode(self):
        """Setup audio mode selection"""
        mode_frame = self.create_labeled_frame("Audio Reactive Mode")

        self.audio_mode = tk.StringVar(value="rms_both")

        modes = [
            ("rms_both", "RMS: Volume -> Brightness + Color"),
            ("rms_brightness", "RMS: Volume -> Brightness Only"),
            ("beat_color", "Beat Detection -> Color Changes"),
            ("beat_white_flash", "Beat Detection -> White Flash"),
            ("frequency_bands", "Frequency Bands -> Rainbow")
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

        # BPM display
        self.bpm_label = ttk.Label(
            mode_frame,
            text="BPM: --",
            font=("Arial", 10, "bold")
        )
        self.bpm_label.pack(anchor=tk.W, pady=(5, 0))

        # Export to controller
        self.controller.audio_mode = self.audio_mode
        self.controller.beat_sensitivity = self.beat_sensitivity
        self.controller.bpm_label = self.bpm_label

    def _setup_visualization(self):
        """Setup audio visualization"""
        viz_frame = self.create_labeled_frame("Audio Level Visualization")

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
        ttk.Radiobutton(
            viz_ctrl, text="Levels", variable=self.viz_mode_var, value="levels"
        ).grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(
            viz_ctrl, text="Reactive Spectrum", variable=self.viz_mode_var, value="spectrum"
        ).grid(row=0, column=2, padx=(6, 12), sticky=tk.W)

        # Viz Gain
        ttk.Label(viz_ctrl, text="Viz Gain:").grid(row=1, column=0, sticky=tk.W)
        self.viz_gain_var = tk.DoubleVar(value=2.0)
        ttk.Scale(
            viz_ctrl, from_=0.5, to=4.0, variable=self.viz_gain_var,
            orient=tk.HORIZONTAL, length=180
        ).grid(row=1, column=1, padx=(6, 12), sticky=tk.W)

        # Bars count
        ttk.Label(viz_ctrl, text="Bars:").grid(row=1, column=2, sticky=tk.W)
        self.viz_bars_var = tk.IntVar(value=40)
        ttk.Scale(
            viz_ctrl, from_=10, to=80, variable=self.viz_bars_var,
            orient=tk.HORIZONTAL, length=180
        ).grid(row=1, column=3, padx=(6, 0), sticky=tk.W)

        # Sensitivity label
        self.sens_label_var = tk.StringVar(value="Medium")
        ttk.Label(viz_frame, textvariable=self.sens_label_var).pack(anchor=tk.W, pady=(6, 0))

        # Export to controller
        self.controller.audio_canvas = self.audio_canvas
        self.controller.viz_mode_var = self.viz_mode_var
        self.controller.viz_gain_var = self.viz_gain_var
        self.controller.viz_bars_var = self.viz_bars_var
        self.controller.sens_label_var = self.sens_label_var

    def _setup_device_selection(self):
        """Setup audio device selection"""
        device_frame = self.create_labeled_frame("Audio Input Device")

        ttk.Label(device_frame, text="Select Input Device:").pack(anchor=tk.W, pady=(0, 5))

        audio_processor = self.controller.audio_processor

        if audio_processor.audio_devices:
            dev_names = [d[1] for d in audio_processor.audio_devices]
            dev_ids = [d[0] for d in audio_processor.audio_devices]

            self.device_combo = ttk.Combobox(
                device_frame, values=dev_names, state="readonly"
            )
            self.device_combo.pack(fill=tk.X, pady=(0, 5))

            # Set default device
            default_idx = audio_processor.get_default_input_device_index()
            try:
                list_pos = next((i for i, v in enumerate(dev_ids) if v == default_idx), 0)
                self.device_combo.current(list_pos)
            except Exception:
                self.device_combo.current(0)

            self.device_combo.bind("<<ComboboxSelected>>", self.on_audio_device_change)

            # Restart button
            ttk.Button(
                device_frame,
                text="Restart Audio Service",
                command=self.restart_audio_service
            ).pack(fill=tk.X)

            self.controller.device_combo = self.device_combo
        else:
            ttk.Label(device_frame, text="No audio devices found").pack()

    def _setup_sync_controls(self):
        """Setup music sync control"""
        sync_frame = self.create_labeled_frame("Music Synchronization")

        ttk.Label(
            sync_frame,
            text="Choose how the lamp reacts to audio input"
        ).pack(pady=(0, 10))

        self.mic_btn = ttk.Button(
            sync_frame,
            text="Start Music Sync",
            command=self.toggle_audio_sync
        )
        self.mic_btn.pack(fill=tk.X)

        # Export to controller
        self.controller.mic_btn = self.mic_btn

    # Event handlers
    def on_audio_device_change(self, event):
        """Handle audio device change"""
        audio_processor = self.controller.audio_processor

        sel_idx = self.device_combo.current()
        if sel_idx >= 0:
            dev_id = audio_processor.audio_devices[sel_idx][0]
            audio_processor.set_device(dev_id)

            if audio_processor.mic_running:
                audio_processor.restart()

    def restart_audio_service(self):
        """User-triggered restart of audio service"""
        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "PyAudio not available")
            return
        self.controller.audio_processor.restart()

    def toggle_audio_sync(self):
        """Toggle audio synchronization"""
        if not self.check_connection():
            return

        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "PyAudio not available")
            return

        audio_processor = self.controller.audio_processor

        if audio_processor.mic_running:
            audio_processor.stop_listening()
            self.effects_engine.stop_audio_effect()
            self.mic_btn.config(text="Start Music Sync")
        else:
            # Get brightness from color tab
            brightness = 1000
            if hasattr(self.controller, 'color_bright_var'):
                brightness = int(self.controller.color_bright_var.get())

            self.effects_engine.set_audio_parameters(
                mode=self.audio_mode.get(),
                sensitivity=self.beat_sensitivity.get(),
                brightness=brightness
            )

            if audio_processor.start_listening():
                self.effects_engine.start_audio_effect()
                self.mic_btn.config(text="Stop Music Sync")
                self.controller._reset_effect_buttons('music')
