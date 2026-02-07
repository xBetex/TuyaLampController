#!/usr/bin/env python3
"""
White Strobe Effect - Pure white flashing strobe
"""

import time
from .base_effect import BaseEffect


class WhiteStrobeEffect(BaseEffect):
    """White-only strobe effect"""

    def __init__(self, device_manager):
        super().__init__(device_manager, "White Strobe")

    def _loop(self):
        """White Strobe effect loop"""
        while self.running:
            try:
                # Calculate delay based on speed
                # Speed 1-100. 100 = fast (0.05s), 1 = slow (1.0s)
                delay = max(0.05, 0.6 - (self.speed / 100.0) * 0.55)

                # ON Phase - White
                r, g, b = 255, 255, 255

                # Apply brightness
                r_out, g_out, b_out = self._apply_brightness(r, g, b)

                self.device_manager.set_color(r_out, g_out, b_out)

                hex_color = self._rgb_to_hex(r_out, g_out, b_out)
                self._notify_color(hex_color)

                time.sleep(delay)

                # OFF Phase
                self.device_manager.set_color(0, 0, 0)
                self._notify_color("#000000")

                time.sleep(delay)

            except Exception as e:
                self.logger.error(f"White strobe effect error: {e}")
                time.sleep(1.0)
