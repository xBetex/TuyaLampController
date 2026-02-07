"""
Ambilight (Screen Sync) module for Smart Lamp Controller
"""
import threading
import time
import logging
import numpy as np
from typing import Optional, Callable

try:
    import mss
    import cv2
    AMBILIGHT_AVAILABLE = True
except ImportError:
    AMBILIGHT_AVAILABLE = False

class AmbilightProcessor:
    """Handles screen capture and color extraction for Ambilight effect"""
    
    def __init__(self):
        self.running = False
        self.active = False
        self.logger = logging.getLogger(__name__)
        
        # Parameters
        self.alpha = 0.2  # Smoothing factor (0.15 - 0.3)
        self.fps_limit = 12  # Reduced to 12 FPS to avoid flooding Tuya lamps
        self.sample_res = (64, 36)
        self.monitor_index = 1  # Default to primary monitor
        self.mode = "average"  # "average" or "accent"
        self.crop_percent = 15  # Percentage to crop from each edge (ignore taskbar/headers)

        # Color change detection threshold (RGB distance 0-1 scale)
        # Only send updates when color changed by more than this amount
        self.color_change_threshold = 0.03  # ~3% difference in RGB space

        # State
        self.prev_color = np.array([0.0, 0.0, 0.0])
        self.last_sent_color = np.array([0.0, 0.0, 0.0])  # Last color actually sent to device
        self.current_rgb = (0, 0, 0)
        self.thread: Optional[threading.Thread] = None

        # Callbacks
        self.color_callback: Optional[Callable[[int, int, int], None]] = None

    def start(self, color_callback: Callable[[int, int, int], None]):
        """Start the ambilight processing thread"""
        if not AMBILIGHT_AVAILABLE:
            self.logger.error("mss or opencv-python not installed")
            return False
            
        if self.running:
            return True
            
        self.color_callback = color_callback
        self.running = True
        self.active = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        self.logger.info("Ambilight processor started")
        return True

    def stop(self):
        """Stop the ambilight processing"""
        self.active = False
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.logger.info("Ambilight processor stopped")

    def _worker(self):
        """Main capture and processing loop"""
        try:
            with mss.mss() as sct:
                while self.running:
                    if not self.active:
                        time.sleep(0.1)
                        continue
                    
                    # Ensure monitor index is valid
                    if self.monitor_index >= len(sct.monitors):
                        self.monitor_index = 1
                    monitor = sct.monitors[self.monitor_index]
                        
                    start_time = time.time()
                    
                    # 1. Capture screen
                    img_sct = sct.grab(monitor)
                    # Convert to BGRA numpy array and then to BGR
                    img = np.array(img_sct)[:, :, :3]

                    # 1b. Edge Cropping (Ignore taskbar, headers, etc)
                    if self.crop_percent > 0:
                        h_orig, w_orig = img.shape[:2]
                        margin_h = int(h_orig * self.crop_percent / 100)
                        margin_w = int(w_orig * self.crop_percent / 100)
                        # Crop: remove margins but keep center
                        img = img[margin_h:h_orig-margin_h, margin_w:w_orig-margin_w]
                    
                    # 2. Downscale for performance
                    small = cv2.resize(img, self.sample_res, interpolation=cv2.INTER_AREA)
                    
                    # 3. Extract Dominant Color
                    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
                    h, s, v = cv2.split(hsv)
                    
                    # Mask out very dark or very desaturated pixels
                    mask = (v > 30) & (s > 20)
                    
                    if np.any(mask):
                        if self.mode == "accent":
                            # Primary/Accent color mode: Find the most frequent saturated hue
                            accent_mask = (v > 40) & (s > 50)
                            if np.any(accent_mask):
                                hues = h[accent_mask]
                                hist, bins = np.histogram(hues, bins=18, range=(0, 180))
                                dominant_bin = np.argmax(hist)
                                
                                # Dominance check: Is this color > 30% of the saturated screen?
                                total_saturated = len(hues)
                                dominance = hist[dominant_bin] / total_saturated if total_saturated > 0 else 0
                                
                                target_h = (bins[dominant_bin] + bins[dominant_bin+1]) / 2
                                
                                if dominance > 0.3:
                                    # Very dominant color (like the deep red #990100)
                                    # Force full vibrancy
                                    target_s = 255
                                    target_v = max(200, v[accent_mask].max())
                                else:
                                    # Balanced accent
                                    bin_mask = (h >= bins[dominant_bin]) & (h < bins[dominant_bin+1]) & accent_mask
                                    avg_s = s[bin_mask].mean() if np.any(bin_mask) else 180
                                    target_s = min(220, avg_s * 1.5)
                                    target_v = v[bin_mask].max() if np.any(bin_mask) else 200
                                
                                hsv_pixel = np.uint8([[[target_h, target_s, target_v]]])
                                rgb_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2RGB)[0][0]
                                target_rgb = rgb_pixel.astype(float)
                            else:
                                # Fallback
                                target_rgb = cv2.cvtColor(np.uint8([[[h[mask].mean(), s[mask].mean(), v[mask].mean()]]]), cv2.COLOR_HSV2RGB)[0][0].astype(float)
                        else:
                            # Standard Average Mode
                            target_rgb = cv2.cvtColor(np.uint8([[[h[mask].mean(), s[mask].mean(), v[mask].mean()]]]), cv2.COLOR_HSV2RGB)[0][0].astype(float)
                    else:
                        target_rgb = np.array([0.0, 0.0, 0.0])
                    
                    # 4. Temporal Smoothing
                    # Accent mode might benefit from slightly slower smoothing to avoid jumps
                    actual_alpha = self.alpha * 0.7 if self.mode == "accent" else self.alpha
                    smoothed = (actual_alpha * target_rgb) + ((1.0 - actual_alpha) * self.prev_color)
                    self.prev_color = smoothed
                    
                    r, g, b = smoothed.astype(int)
                    self.current_rgb = (r, g, b)

                    # 5. Color change detection - only send if color changed significantly
                    # This reduces device flooding when screen content is stable
                    should_send = self._color_changed_significantly(smoothed)

                    if should_send and self.color_callback:
                        self.color_callback(r, g, b)
                        self.last_sent_color = smoothed.copy()
                    
                    # Limit FPS
                    elapsed = time.time() - start_time
                    delay = max(0.001, (1.0 / self.fps_limit) - elapsed)
                    time.sleep(delay)
                    
        except Exception as e:
            self.logger.error(f"Ambilight worker error: {e}")
            self.running = False

    def _color_changed_significantly(self, new_color: np.ndarray) -> bool:
        """
        Check if the new color is significantly different from the last sent color.
        Uses Euclidean distance in normalized RGB space.
        """
        # Normalize to 0-1 range for distance calculation
        old_norm = self.last_sent_color / 255.0
        new_norm = new_color / 255.0

        # Euclidean distance in RGB space
        distance = np.sqrt(np.sum((new_norm - old_norm) ** 2))

        return distance > self.color_change_threshold

    def set_color_change_threshold(self, threshold: float):
        """Set the minimum color change threshold (0.0-1.0)"""
        self.color_change_threshold = max(0.0, min(1.0, threshold))
