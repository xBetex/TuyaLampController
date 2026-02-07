#!/usr/bin/env python3
"""
Smart Ambient Processor - Automatically picks the best color from screen
Uses the intelligent color selection logic to continuously update lamp color
"""

import threading
import time
import logging
from typing import Optional, Callable
from color_selection_logic import ColorSelectionLogic, SCREEN_CAPTURE_AVAILABLE

# Try to import decision report types
try:
    from color_decision import ColorDecisionReport
    COLOR_DECISION_AVAILABLE = True
except ImportError:
    COLOR_DECISION_AVAILABLE = False
    ColorDecisionReport = None

class SmartAmbientProcessor:
    """Automatically picks and applies the best screen color for ambient lighting"""
    
    def __init__(self):
        self.running = False
        self.active = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize color logic
        self.color_logic = ColorSelectionLogic()
        
        # Parameters
        self.update_interval = 1.0  # Update every second
        self.monitor_index = 1  # Default to primary monitor
        self.min_color_change_threshold = 0.1  # Only update if color changed significantly
        
        # State
        self.current_color = "#000000"
        self.last_sent_color = "#000000"
        self.thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.color_callback: Optional[Callable[[str], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None
        self.decision_callback: Optional[Callable[["ColorDecisionReport"], None]] = None

        # Last decision report for UI access
        self.last_decision_report: Optional["ColorDecisionReport"] = None
    
    def start(self, color_callback: Callable[[str], None], status_callback: Optional[Callable[[str], None]] = None,
              decision_callback: Optional[Callable[["ColorDecisionReport"], None]] = None):
        """Start the smart ambient processing"""
        if not SCREEN_CAPTURE_AVAILABLE:
            self.logger.error("Screen capture dependencies not available (mss, pillow, numpy)")
            if status_callback:
                status_callback("Screen capture not available - install mss, pillow, numpy")
            return False

        if self.running:
            return True

        self.color_callback = color_callback
        self.status_callback = status_callback
        self.decision_callback = decision_callback
        self.running = True
        self.active = True
        
        # Start processing thread
        self.thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.thread.start()
        
        self.logger.info("Smart ambient processor started")
        if self.status_callback:
            self.status_callback("🎯 Smart ambient lighting active")
        
        return True
    
    def stop(self):
        """Stop the smart ambient processing"""
        if not self.running:
            return
        
        self.running = False
        self.active = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        self.logger.info("Smart ambient processor stopped")
        if self.status_callback:
            self.status_callback("Smart ambient lighting stopped")
    
    def set_monitor(self, monitor_index: int):
        """Set which monitor to analyze"""
        self.monitor_index = monitor_index
        self.color_logic.monitor_index = monitor_index
        self.logger.info(f"Smart ambient monitor set to {monitor_index}")
    
    def set_update_interval(self, interval: float):
        """Set how often to update the color (in seconds)"""
        self.update_interval = max(0.5, min(5.0, interval))  # Clamp between 0.5-5 seconds
        self.logger.info(f"Smart ambient update interval set to {self.update_interval}s")
    
    def _processing_loop(self):
        """Main processing loop - runs in background thread"""
        consecutive_failures = 0
        max_failures = 5
        
        while self.running:
            try:
                # Capture screen thumbnail
                self.color_logic.capture_screen_thumbnail()
                
                # Get dominant colors (filtered - no grays/blacks)
                dominant_colors = self.color_logic.get_dominant_colors(8)
                
                if dominant_colors:
                    # Find the best color with detailed report
                    best_color, decision_report = self.color_logic.get_best_ambient_color_with_report(dominant_colors)

                    # Store last report for UI access
                    if decision_report:
                        self.last_decision_report = decision_report

                        # Notify decision callback
                        if self.decision_callback:
                            try:
                                self.decision_callback(decision_report)
                            except Exception as e:
                                self.logger.warning(f"Decision callback error: {e}")

                    if best_color:
                        # Check if color changed significantly
                        if self._color_changed_significantly(best_color):
                            self.current_color = best_color
                            self.last_sent_color = best_color

                            # Send to lamp
                            if self.color_callback:
                                self.color_callback(best_color)

                            # Find percentage for status
                            color_percentage = next((p for c, p in dominant_colors if c == best_color), 0)

                            if self.status_callback:
                                self.status_callback(f"Auto-applied: {best_color} ({color_percentage:.1f}% of screen)")

                            self.logger.debug(f"Smart ambient applied color: {best_color}")

                        consecutive_failures = 0
                    else:
                        # No suitable colors found
                        if consecutive_failures == 0:  # Only log first failure
                            if self.status_callback:
                                self.status_callback("No suitable colors found - screen mostly grayscale")
                        consecutive_failures += 1
                else:
                    # No colors found at all
                    if consecutive_failures == 0:
                        if self.status_callback:
                            self.status_callback("No colors detected on screen")
                    consecutive_failures += 1
                
                # Reset failure count if we had too many
                if consecutive_failures >= max_failures:
                    consecutive_failures = 0  # Reset to avoid spam
                
            except Exception as e:
                self.logger.error(f"Smart ambient processing error: {e}")
                consecutive_failures += 1
                
                if consecutive_failures >= max_failures:
                    if self.status_callback:
                        self.status_callback(f"❌ Smart ambient error: {str(e)}")
                    consecutive_failures = 0
            
            # Wait for next update
            time.sleep(self.update_interval)
    
    def _color_changed_significantly(self, new_color: str) -> bool:
        """Check if the new color is significantly different from the last sent color"""
        if self.last_sent_color == "#000000":  # First color
            return True
        
        try:
            # Convert both colors to RGB
            old_r = int(self.last_sent_color[1:3], 16) / 255
            old_g = int(self.last_sent_color[3:5], 16) / 255
            old_b = int(self.last_sent_color[5:7], 16) / 255
            
            new_r = int(new_color[1:3], 16) / 255
            new_g = int(new_color[3:5], 16) / 255
            new_b = int(new_color[5:7], 16) / 255
            
            # Calculate Euclidean distance in RGB space
            distance = ((new_r - old_r)**2 + (new_g - old_g)**2 + (new_b - old_b)**2)**0.5
            
            return distance > self.min_color_change_threshold
            
        except Exception:
            return True  # If calculation fails, assume it changed
    
    def get_current_color(self) -> str:
        """Get the current color being used"""
        return self.current_color
    
    def is_running(self) -> bool:
        """Check if the processor is running"""
        return self.running and self.active

    def get_last_decision_report(self) -> Optional["ColorDecisionReport"]:
        """Get the most recent decision report for UI display"""
        return self.last_decision_report

    def set_decision_callback(self, callback: Optional[Callable[["ColorDecisionReport"], None]]):
        """Set or update the decision callback"""
        self.decision_callback = callback