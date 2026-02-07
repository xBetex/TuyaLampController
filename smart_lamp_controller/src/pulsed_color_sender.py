#!/usr/bin/env python3
"""
Pulsed Color Sender - Sends 4 packets per second with 250ms intervals
Rate-limited to 1 second intervals
"""

import threading
import time
import logging
from typing import Callable, Optional


class PulsedColorSender:
    """Sends color with 4 pulses per second, rate-limited to 1 second intervals"""

    def __init__(self, color_callback: Optional[Callable[[str], None]] = None):
        self.color_callback = color_callback
        self.logger = logging.getLogger(__name__)

        # State
        self.running = False
        self.current_color = "#000000"
        self.last_sent_color = "#000000"
        self.last_send_time = 0

        # Pulsing parameters
        self.pulses_per_second = 4
        self.update_pulse_interval()
        self.rate_limit_seconds = 1.0  # Only send once per second

        # Threading
        self.pulse_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

    def start(self):
        """Start the pulsed color sending"""
        if self.running:
            return

        self.running = True
        self.stop_event.clear()

        # Start pulse thread
        self.pulse_thread = threading.Thread(target=self._pulse_loop, daemon=True)
        self.pulse_thread.start()

        self.logger.info("Pulsed color sender started (4 pulses/sec, 1 sec rate limit)")

    def stop(self):
        """Stop the pulsed color sending"""
        if not self.running:
            return

        self.running = False
        self.stop_event.set()

        if self.pulse_thread and self.pulse_thread.is_alive():
            self.pulse_thread.join(timeout=1.0)

        self.logger.info("Pulsed color sender stopped")

    def set_color(self, color: str):
        """Set the current color to send"""
        self.current_color = color

    def set_pulses_per_second(self, pps: int):
        """Set pulses per second and update interval"""
        self.pulses_per_second = max(1, min(8, pps))  # Clamp between 1-8 PPS
        self.update_pulse_interval()
        self.logger.info(
            f"Pulse rate set to {self.pulses_per_second} PPS ({self.pulse_interval_ms}ms interval)"
        )

    def update_pulse_interval(self):
        """Update pulse interval based on PPS"""
        if self.pulses_per_second > 0:
            self.pulse_interval_ms = int(1000.0 / self.pulses_per_second)
        else:
            self.pulse_interval_ms = 1000  # Default to 1 second

    def _pulse_loop(self):
        """Main pulse loop - runs in background thread"""
        pulse_count = 0
        current_batch_start = time.time()

        while self.running and not self.stop_event.is_set():
            current_time = time.time()

            # Check if we should send (rate limit: once per second)
            time_since_batch = current_time - current_batch_start

            if time_since_batch >= self.rate_limit_seconds:
                # Start new batch - reset pulse count
                pulse_count = 0
                current_batch_start = current_time
                self.last_sent_color = self.current_color

            # Send pulse if we haven't exceeded the rate limit
            if (
                pulse_count < self.pulses_per_second
                and self.current_color != self.last_sent_color
            ):
                self._send_color_pulse(self.current_color)
                pulse_count += 1
                self.last_sent_color = self.current_color

            # Wait for next pulse
            self.stop_event.wait(self.pulse_interval_ms / 1000.0)

    def _send_color_pulse(self, color: str):
        """Send a single color pulse"""
        if self.color_callback:
            try:
                self.color_callback(color)
                self.logger.debug(f"Sent color pulse: {color}")
            except Exception as e:
                self.logger.error(f"Error sending color pulse: {e}")

    def is_running(self) -> bool:
        """Check if the pulsed sender is running"""
        return (
            self.running
            and (self.pulse_thread is not None)
            and self.pulse_thread.is_alive()
        )
