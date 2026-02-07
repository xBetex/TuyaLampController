#!/usr/bin/env python3
"""
Base Effect - Template pattern for visual effects
All effects inherit from this class and implement the _loop method
"""

import threading
import logging
from abc import ABC, abstractmethod
from typing import Optional, Callable, List


class BaseEffect(ABC):
    """
    Base class for all visual effects.
    Provides common start/stop logic and callback management.
    """

    def __init__(self, device_manager, name: str):
        self.device_manager = device_manager
        self.name = name
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # Effect parameters (to be set by subclasses or engine)
        self.speed: float = 50.0
        self.brightness: int = 1000  # 0-1000 scale

        # Callbacks
        self.color_callbacks: List[Callable[[str], None]] = []
        self.status_callbacks: List[Callable[[str], None]] = []

    def add_color_callback(self, callback: Callable[[str], None]):
        """Add callback for color preview updates"""
        if callback not in self.color_callbacks:
            self.color_callbacks.append(callback)

    def add_status_callback(self, callback: Callable[[str], None]):
        """Add callback for effect status updates"""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)

    def _notify_color(self, hex_color: str):
        """Notify all color callbacks"""
        for callback in self.color_callbacks:
            try:
                callback(hex_color)
            except Exception as e:
                self.logger.error(f"Color callback error: {e}")

    def _notify_status(self, status: str):
        """Notify all status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")

    def start(self) -> bool:
        """Start the effect. Returns True if started successfully."""
        if self.running:
            return True

        self.running = True

        # Ensure device is in color mode
        self.device_manager.set_mode("colour")

        # Start effect thread
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        self._notify_status(f"{self.name} effect started")
        self.logger.info(f"{self.name} effect started")
        return True

    def stop(self):
        """Stop the effect"""
        if not self.running:
            return

        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)

        self._notify_status(f"{self.name} effect stopped")
        self.logger.info(f"{self.name} effect stopped")

    def _run_loop(self):
        """Internal loop wrapper with error handling"""
        try:
            self._loop()
        except Exception as e:
            self.logger.error(f"{self.name} effect error: {e}")
            self.running = False
            self._notify_status(f"{self.name} effect error: {e}")

    @abstractmethod
    def _loop(self):
        """
        Main effect loop. Must be implemented by subclasses.
        Should check self.running and exit when False.
        """
        pass

    def set_speed(self, speed: float):
        """Set effect speed (1-100)"""
        self.speed = max(1, min(100, speed))

    def set_brightness(self, brightness: int):
        """Set effect brightness (0-1000)"""
        self.brightness = max(0, min(1000, brightness))

    def is_running(self) -> bool:
        """Check if effect is currently running"""
        return self.running

    def _apply_brightness(self, r: float, g: float, b: float) -> tuple:
        """Apply brightness to RGB values"""
        v = self.brightness / 1000.0
        return (r * v, g * v, b * v)

    def _rgb_to_hex(self, r: float, g: float, b: float) -> str:
        """Convert RGB (0-255) to hex string"""
        return '#{:02x}{:02x}{:02x}'.format(
            int(max(0, min(255, r))),
            int(max(0, min(255, g))),
            int(max(0, min(255, b)))
        )
