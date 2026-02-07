#!/usr/bin/env python3
"""
Blinker Effect - Party mode with random color changes
"""

import random
import time
from .base_effect import BaseEffect


class BlinkerEffect(BaseEffect):
    """Random color blinker/party mode effect"""

    # Standard party colors
    PARTY_COLORS = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (0, 255, 255),  # Cyan
        (255, 0, 255),  # Magenta
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
    ]

    def __init__(self, device_manager):
        super().__init__(device_manager, "Blinker")

    def _loop(self):
        """Blinker effect loop (Party Mode)"""
        last_idx = -1

        while self.running:
            try:
                # Calculate delay based on speed
                # Speed 1-100. 100 = fast (0.05s), 1 = slow (2.0s)
                delay = max(0.05, 1.0 - (self.speed / 100.0) * 0.95)

                # Pick a random color different from the last one
                idx = random.randint(0, len(self.PARTY_COLORS) - 1)
                while idx == last_idx and len(self.PARTY_COLORS) > 1:
                    idx = random.randint(0, len(self.PARTY_COLORS) - 1)
                last_idx = idx

                r, g, b = self.PARTY_COLORS[idx]

                # Apply brightness
                r_out, g_out, b_out = self._apply_brightness(r, g, b)

                self.device_manager.set_color(r_out, g_out, b_out)

                hex_color = self._rgb_to_hex(r_out, g_out, b_out)
                self._notify_color(hex_color)

                time.sleep(delay)

            except Exception as e:
                self.logger.error(f"Blinker effect error: {e}")
                time.sleep(1.0)
