#!/usr/bin/env python3
"""
Strobe Effect - Party mode with on/off flashing
"""

import random
import time
from .base_effect import BaseEffect


class StrobeEffect(BaseEffect):
    """Strobe/flash effect with color cycling"""

    # Standard party colors plus white for strobe pop
    PARTY_COLORS = [
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (255, 255, 0),    # Yellow
        (0, 255, 255),    # Cyan
        (255, 0, 255),    # Magenta
        (255, 128, 0),    # Orange
        (128, 0, 255),    # Purple
        (255, 255, 255),  # White (added for strobe pop)
    ]

    def __init__(self, device_manager):
        super().__init__(device_manager, "Strobe")

    def _loop(self):
        """Strobe effect loop (On/Off Party Mode)"""
        while self.running:
            try:
                # Calculate delay based on speed
                # Speed 1-100. 100 = fast (0.05s), 1 = slow (1.0s)
                delay = max(0.05, 0.6 - (self.speed / 100.0) * 0.55)

                # ON Phase - random color
                idx = random.randint(0, len(self.PARTY_COLORS) - 1)
                r, g, b = self.PARTY_COLORS[idx]

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
                self.logger.error(f"Strobe effect error: {e}")
                time.sleep(1.0)
