#!/usr/bin/env python3
"""
Rainbow Effect - Smooth color cycling through the spectrum
"""

import colorsys
import time
from typing import List
from .base_effect import BaseEffect


class RainbowEffect(BaseEffect):
    """Cycles through colors smoothly like a rainbow"""

    def __init__(self, device_manager):
        super().__init__(device_manager, "Rainbow")

        # Rainbow-specific parameters
        self.h_min: float = 0.0
        self.h_max: float = 1.0
        self.custom_colors: List[str] = []
        self.use_custom_colors: bool = False

    def set_hue_range(self, h_min: float, h_max: float):
        """Set the hue range for rainbow cycling"""
        self.h_min = max(0.0, min(1.0, h_min))
        self.h_max = max(0.0, min(1.0, h_max))
        if self.h_min >= self.h_max:
            self.h_max = self.h_min + 0.1

    def set_custom_colors(self, colors: List[str], use_custom: bool = True):
        """Set custom color stops for the rainbow"""
        self.custom_colors = colors
        self.use_custom_colors = use_custom

    def _loop(self):
        """Rainbow effect loop"""
        color_index = 0
        hue = self.h_min

        while self.running:
            try:
                # Calculate delay based on speed
                delay = max(0.01, 0.2 - (self.speed / 600.0))

                if self.use_custom_colors and self.custom_colors:
                    # Use custom color sequence
                    color_hex = self.custom_colors[color_index]
                    r = int(color_hex[1:3], 16)
                    g = int(color_hex[3:5], 16)
                    b = int(color_hex[5:7], 16)

                    # Apply brightness
                    r_out, g_out, b_out = self._apply_brightness(r, g, b)

                    self.device_manager.set_color(r_out, g_out, b_out)
                    self._notify_color(color_hex)

                    color_index = (color_index + 1) % len(self.custom_colors)
                    time.sleep(delay * 10)  # Slower for custom colors

                else:
                    # Use HSV rainbow
                    hue += 0.005
                    if hue > self.h_max:
                        hue = self.h_min

                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)

                    # Apply brightness
                    r_out, g_out, b_out = self._apply_brightness(r * 255, g * 255, b * 255)

                    self.device_manager.set_color(r_out, g_out, b_out)

                    hex_color = self._rgb_to_hex(r_out, g_out, b_out)
                    self._notify_color(hex_color)

                    time.sleep(delay)

            except Exception as e:
                self.logger.error(f"Rainbow effect error: {e}")
                break
