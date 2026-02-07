"""
Effects engine for Smart Lamp Controller
"""
import threading
import time
import colorsys
import logging
from typing import List, Optional, Callable
from queue import Queue
from ambilight_processor import AmbilightProcessor, AMBILIGHT_AVAILABLE
from smart_ambient_processor import SmartAmbientProcessor

class EffectsEngine:
    """Manages visual effects for the smart lamp"""
    
    def __init__(self, device_manager, audio_processor):
        self.device_manager = device_manager
        self.audio_processor = audio_processor
        
        # Effect state
        self.active_effect = "static"
        self.rainbow_running = False
        self.blinker_running = False
        self.strobe_running = False
        self.white_strobe_running = False
        self.ambilight_running = False
        self.smart_ambient_running = False
        self.last_hsv = (0.0, 1.0, 1.0)
        
        # Components
        self.ambilight_processor = AmbilightProcessor() if AMBILIGHT_AVAILABLE else None
        self.smart_ambient_processor = SmartAmbientProcessor()
        self.smart_send_rate_limit = 0.0  # seconds; 0 = unlimited
        self._smart_last_send_ts = 0.0
        
        # Rainbow effect parameters
        self.rainbow_speed = 50
        self.rainbow_h_min = 0.0
        self.rainbow_h_max = 1.0
        self.rainbow_color_stops: List[str] = []
        self.use_custom_colors = False
        
        # Blinker effect parameters
        # Blinker effect parameters
        self.blinker_speed = 50

        # Strobe effect parameters
        self.strobe_speed = 80
        
        # White Strobe effect parameters
        self.white_strobe_speed = 80

        
        # Audio effect parameters
        self.audio_mode = "rms_both"
        self.beat_sensitivity = 2.5
        self.color_brightness = 1000
        
        # Callbacks for UI updates
        self.color_callbacks: List[Callable[[str], None]] = []
        self.status_callbacks: List[Callable[[str], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Effect threads
        # Effect threads
        self.rainbow_thread: Optional[threading.Thread] = None
        self.blinker_thread: Optional[threading.Thread] = None
        self.strobe_thread: Optional[threading.Thread] = None
        self.white_strobe_thread: Optional[threading.Thread] = None
        self.audio_thread: Optional[threading.Thread] = None
    
    def add_color_callback(self, callback: Callable[[str], None]):
        """Add callback for color preview updates"""
        self.color_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable[[str], None]):
        """Add callback for effect status updates"""
        self.status_callbacks.append(callback)
    
    def _notify_color_callbacks(self, hex_color: str):
        """Notify all color callbacks"""
        for callback in self.color_callbacks:
            try:
                callback(hex_color)
            except Exception as e:
                self.logger.error(f"Color callback error: {e}")
    
    def _notify_status_callbacks(self, status: str):
        """Notify all status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    def set_static_color(self, r: float, g: float, b: float, brightness: Optional[float] = None):
        """Set a static color"""
        if brightness is not None:
            # Apply brightness to RGB values
            r, g, b = r * brightness, g * brightness, b * brightness
        
        self.device_manager.set_color(r, g, b)
        
        # Update HSV state
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        self.last_hsv = (h, s, v)
        
        # Notify UI
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(r), int(g), int(b))
        self._notify_color_callbacks(hex_color)
        
        self.active_effect = "color"
        self._notify_status_callbacks("Static color set")
    
    def set_color_from_hex(self, hex_color: str, brightness: Optional[float] = None):
        """Set color from hex string"""
        try:
            # Convert hex to RGB
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            self.set_static_color(r, g, b, brightness)
        except ValueError as e:
            self.logger.error(f"Invalid hex color: {hex_color}")
    
    def start_rainbow_effect(self):
        """Start rainbow effect"""
        if self.rainbow_running:
            return
        
        # Stop other effects
        self.stop_audio_effect()
        self.stop_blinker_effect()
        self.stop_strobe_effect()
        self.stop_white_strobe_effect()
        self.stop_ambilight_effect()
        
        self.rainbow_running = True
        self.active_effect = "rainbow"
        
        # Ensure device is in color mode
        self.device_manager.set_mode("colour")
        
        # Start rainbow thread
        self.rainbow_thread = threading.Thread(target=self._rainbow_loop, daemon=True)
        self.rainbow_thread.start()
        
        self._notify_status_callbacks("Rainbow effect started")
    
    def stop_rainbow_effect(self):
        """Stop rainbow effect"""
        self.rainbow_running = False
        self.active_effect = "static"
        
        if self.rainbow_thread and self.rainbow_thread.is_alive():
            self.rainbow_thread.join(timeout=1.0)
        
        self._notify_status_callbacks("Rainbow effect stopped")
    
    def _rainbow_loop(self):
        """Rainbow effect loop"""
        color_index = 0
        hue = self.rainbow_h_min
        
        while self.rainbow_running:
            try:
                # Calculate delay based on speed
                delay = max(0.01, 0.2 - (self.rainbow_speed / 600.0))
                
                if self.use_custom_colors and self.rainbow_color_stops:
                    # Use custom color sequence
                    color_hex = self.rainbow_color_stops[color_index]
                    rgb = tuple(int(color_hex[i:i+2], 16) for i in (1, 3, 5))
                    
                    # Apply brightness
                    v = self.color_brightness / 1000.0
                    r, g, b = [c * v for c in rgb]
                    
                    self.device_manager.set_color(r, g, b)
                    self._notify_color_callbacks(color_hex)
                    
                    color_index = (color_index + 1) % len(self.rainbow_color_stops)
                    time.sleep(delay * 10)  # Slower for custom colors
                    
                else:
                    # Use HSV rainbow
                    h_min, h_max = self.rainbow_h_min, self.rainbow_h_max
                    if h_min >= h_max:
                        h_max = h_min + 0.1
                    
                    hue += 0.005
                    if hue > h_max:
                        hue = h_min
                    
                    v = self.color_brightness / 1000.0
                    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                    
                    self.device_manager.set_color(r*255, g*255, b*255)
                    hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
                    self._notify_color_callbacks(hex_color)
                    
                    time.sleep(delay)
                    
            except Exception as e:
                self.logger.error(f"Rainbow effect error: {e}")
                break
    
    def start_audio_effect(self):
        """Start audio-reactive effect"""
        if not self.audio_processor.mic_running:
            self.logger.warning("Audio processor not running")
            return
        
        # Stop other effects
        self.stop_rainbow_effect()
        self.stop_blinker_effect()
        self.stop_strobe_effect()
        self.stop_white_strobe_effect()
        self.stop_ambilight_effect()
        
        self.active_effect = "music"
        
        # Ensure device is in color mode
        self.device_manager.set_mode("colour")
        
        # Start audio effect thread
        self.audio_thread = threading.Thread(target=self._audio_effect_loop, daemon=True)
        self.audio_thread.start()
        
        self._notify_status_callbacks("Audio effect started")
    
    def stop_audio_effect(self):
        """Stop audio-reactive effect"""
        self.active_effect = "static"
        
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)
        
        self._notify_status_callbacks("Audio effect stopped")
    
    def _audio_effect_loop(self):
        """Audio-reactive effect loop"""
        hue = 0.0
        
        while self.active_effect == "music":
            try:
                # Get audio data
                audio_data = self.audio_processor.get_audio_mode_data(
                    self.audio_mode, self.beat_sensitivity
                )
                
                if not audio_data:
                    time.sleep(0.1)
                    continue
                
                levels = audio_data.get('levels', [])
                if not levels:
                    time.sleep(0.1)
                    continue
                
                current_level = levels[-1]  # Most recent level
                
                if self.audio_mode == "rms_both":
                    # RMS controls both brightness and color
                    if current_level > 0.1:
                        if current_level > 0.5 and audio_data.get('beat_detected', False):
                            hue = (hue + 0.15) % 1.0
                        
                        v = min(1.0, current_level * 2)
                        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                        self.device_manager.set_color(r*255, g*255, b*255)
                        hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
                        self._notify_color_callbacks(hex_color)
                
                elif self.audio_mode == "rms_brightness":
                    # RMS only controls brightness
                    if current_level > 0.1:
                        v = min(1.0, current_level * 2)
                        h, s, _ = self.last_hsv if self.last_hsv else (hue, 1.0)
                        r, g, b = colorsys.hsv_to_rgb(h, s, v)
                        self.device_manager.set_color(r*255, g*255, b*255)
                        hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
                        self._notify_color_callbacks(hex_color)
                
                elif self.audio_mode == "beat_color":
                    # Beat detection changes color
                    if audio_data.get('beat_detected', False):
                        hue = (hue + 0.2) % 1.0
                        v = self.color_brightness / 1000.0
                        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                        self.device_manager.set_color(r*255, g*255, b*255)
                        hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
                        self._notify_color_callbacks(hex_color)
                
                elif self.audio_mode == "frequency_bands":
                    # Frequency bands control color
                    bands = audio_data.get('frequency_bands', [])
                    if bands and max(bands) > 0:
                        dominant_band = bands.index(max(bands))
                        hue = dominant_band / len(bands)
                        
                        # Brightness based on total energy
                        total_energy = sum(bands)
                        v = min(1.0, max(0.1, total_energy / 1000))
                        
                        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                        self.device_manager.set_color(r*255, g*255, b*255)
                        hex_color = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
                        self._notify_color_callbacks(hex_color)

                elif self.audio_mode == "beat_white_flash":
                    # Beat detection flashes white light
                    if audio_data.get('beat_detected', False):
                        # Flash ON
                        v = self.color_brightness / 1000.0
                        self.device_manager.set_color(255*v, 255*v, 255*v)
                        hex_color = '#{:02x}{:02x}{:02x}'.format(int(255*v), int(255*v), int(255*v))
                        self._notify_color_callbacks(hex_color)
                        # Hold the flash briefly
                        time.sleep(0.05) 
                    else:
                        # Off or very dim when no beat
                        self.device_manager.set_color(0, 0, 0)
                        self._notify_color_callbacks("#000000")
                
                time.sleep(0.05)  # 20 FPS
                
            except Exception as e:
                self.logger.error(f"Audio effect error: {e}")
                time.sleep(0.1)
    
    def set_rainbow_parameters(self, speed: float, h_min: float, h_max: float, 
                              custom_colors: List[str] = None, use_custom: bool = False):
        """Set rainbow effect parameters"""
        self.rainbow_speed = speed
        self.rainbow_h_min = h_min
        self.rainbow_h_max = h_max
        self.use_custom_colors = use_custom
        
        if custom_colors is not None:
            self.rainbow_color_stops = custom_colors
    
    def set_blinker_parameters(self, speed: float):
        """Set blinker effect parameters"""
        self.blinker_speed = speed

    def start_blinker_effect(self):
        """Start blinker effect"""
        if self.blinker_running:
            return
        
        # Stop other effects
        self.stop_audio_effect()
        self.stop_rainbow_effect()
        self.stop_strobe_effect()
        self.stop_white_strobe_effect()
        self.stop_ambilight_effect()
        
        self.blinker_running = True
        self.active_effect = "blinker"
        
        # Ensure device is in color mode
        self.device_manager.set_mode("colour")
        
        # Start blinker thread
        self.blinker_thread = threading.Thread(target=self._blinker_loop, daemon=True)
        self.blinker_thread.start()
        
        self._notify_status_callbacks("Blinker effect started")
    
    def stop_blinker_effect(self):
        """Stop blinker effect"""
        self.blinker_running = False
        if self.active_effect == "blinker":
            self.active_effect = "static"
        
        if self.blinker_thread and self.blinker_thread.is_alive():
            self.blinker_thread.join(timeout=1.0)
        
        self._notify_status_callbacks("Blinker effect stopped")

    def _blinker_loop(self):
        """Blinker effect loop (Party Mode)"""
        import random
        
        # Standard party colors
        party_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
            (255, 0, 255),  # Magenta
            (255, 128, 0),  # Orange
            (128, 0, 255),  # Purple
        ]
        
        last_idx = -1
        
        while self.blinker_running:
            try:
                # Calculate delay based on speed (simulated Hz or strict timing)
                # Speed 1-100. 100 = fast (0.1s), 1 = slow (2.0s)
                delay = max(0.05, 1.0 - (self.blinker_speed / 100.0) * 0.95)
                
                # Pick a random color different from the last one
                idx = random.randint(0, len(party_colors) - 1)
                while idx == last_idx and len(party_colors) > 1:
                    idx = random.randint(0, len(party_colors) - 1)
                last_idx = idx
                
                r, g, b = party_colors[idx]
                
                # Apply global brightness
                v = self.color_brightness / 1000.0
                r_out, g_out, b_out = r * v, g * v, b * v
                
                self.device_manager.set_color(r_out, g_out, b_out)
                
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(r_out), int(g_out), int(b_out))
                self._notify_color_callbacks(hex_color)
                
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Blinker effect error: {e}")
                time.sleep(1.0)
    
    def set_strobe_parameters(self, speed: float):
        """Set strobe effect parameters"""
        self.strobe_speed = speed

    def start_strobe_effect(self):
        """Start strobe effect"""
        if self.strobe_running:
            return
        
        # Stop other effects
        self.stop_audio_effect()
        self.stop_rainbow_effect()
        self.stop_blinker_effect()
        self.stop_white_strobe_effect()
        self.stop_ambilight_effect()
        
        self.strobe_running = True
        self.active_effect = "strobe"
        
        # Ensure device is in color mode
        self.device_manager.set_mode("colour")
        
        # Start strobe thread
        self.strobe_thread = threading.Thread(target=self._strobe_loop, daemon=True)
        self.strobe_thread.start()
        
        self._notify_status_callbacks("Strobe effect started")
    
    def stop_strobe_effect(self):
        """Stop strobe effect"""
        self.strobe_running = False
        if self.active_effect == "strobe":
            self.active_effect = "static"
        
        if self.strobe_thread and self.strobe_thread.is_alive():
            self.strobe_thread.join(timeout=1.0)
        
        self._notify_status_callbacks("Strobe effect stopped")

    def _strobe_loop(self):
        """Strobe effect loop (On/Off Party Mode)"""
        import random
        
        # Standard party colors
        party_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (0, 255, 255),  # Cyan
            (255, 0, 255),  # Magenta
            (255, 128, 0),  # Orange
            (128, 0, 255),  # Purple
            (255, 255, 255), # White (added for strobe pop)
        ]
        
        while self.strobe_running:
            try:
                # Calculate delay based on speed
                # Speed 1-100. 100 = fast (0.05s), 1 = slow (1.0s)
                delay = max(0.05, 0.6 - (self.strobe_speed / 100.0) * 0.55)
                
                # ON Phase
                idx = random.randint(0, len(party_colors) - 1)
                r, g, b = party_colors[idx]
                
                # Apply global brightness
                v = self.color_brightness / 1000.0
                r_out, g_out, b_out = r * v, g * v, b * v
                
                self.device_manager.set_color(r_out, g_out, b_out)
                
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(r_out), int(g_out), int(b_out))
                self._notify_color_callbacks(hex_color)
                
                time.sleep(delay)

                # OFF Phase
                self.device_manager.set_color(0, 0, 0)
                # We don't necessarily update callback for OFF or maybe we do? 
                # Updating callback to black might toggle UI weirdly, but let's stick to just light control.
                
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Strobe effect error: {e}")
                time.sleep(1.0)
    
    
    def set_white_strobe_parameters(self, speed: float):
        """Set white strobe effect parameters"""
        self.white_strobe_speed = speed

    def start_white_strobe_effect(self):
        """Start white strobe effect"""
        if self.white_strobe_running:
            return
        
        # Stop other effects
        self.stop_audio_effect()
        self.stop_rainbow_effect()
        self.stop_blinker_effect()
        self.stop_strobe_effect()
        self.stop_ambilight_effect()
        
        self.white_strobe_running = True
        self.active_effect = "white_strobe"
        
        # Ensure device is in color mode (using RGB white for speed)
        self.device_manager.set_mode("colour")
        
        # Start white strobe thread
        self.white_strobe_thread = threading.Thread(target=self._white_strobe_loop, daemon=True)
        self.white_strobe_thread.start()
        
        self._notify_status_callbacks("White strobe effect started")
    
    def stop_white_strobe_effect(self):
        """Stop white strobe effect"""
        self.white_strobe_running = False
        if self.active_effect == "white_strobe":
            self.active_effect = "static"
        
        if self.white_strobe_thread and self.white_strobe_thread.is_alive():
            self.white_strobe_thread.join(timeout=1.0)
        
        self._notify_status_callbacks("White strobe effect stopped")

    def _white_strobe_loop(self):
        """White Strobe effect loop"""
        
        while self.white_strobe_running:
            try:
                # Calculate delay based on speed
                # Speed 1-100. 100 = fast (0.05s), 1 = slow (1.0s)
                delay = max(0.05, 0.6 - (self.white_strobe_speed / 100.0) * 0.55)
                
                # ON Phase - White
                r, g, b = 255, 255, 255
                
                # Apply global brightness
                v = self.color_brightness / 1000.0
                r_out, g_out, b_out = r * v, g * v, b * v
                
                self.device_manager.set_color(r_out, g_out, b_out)
                
                hex_color = '#{:02x}{:02x}{:02x}'.format(int(r_out), int(g_out), int(b_out))
                self._notify_color_callbacks(hex_color)
                
                time.sleep(delay)

                # OFF Phase
                self.device_manager.set_color(0, 0, 0)
                
                time.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"White strobe effect error: {e}")
                time.sleep(1.0)
    
    def start_ambilight_effect(self):
        """Start Ambilight (Screen Sync) effect"""
        if not AMBILIGHT_AVAILABLE or self.ambilight_processor is None:
            self.logger.error("Ambilight not available")
            return
            
        if self.ambilight_running:
            return
            
        # Stop other effects
        self.stop_rainbow_effect()
        self.stop_blinker_effect()
        self.stop_strobe_effect()
        self.stop_white_strobe_effect()
        self.stop_audio_effect()
        
        self.ambilight_running = True
        self.active_effect = "ambilight"
        
        # Ensure device is in color mode
        self.device_manager.set_mode("colour")
        
        # Start ambilight processor with color callback
        self.ambilight_processor.start(self._on_ambilight_color)
        
        self._notify_status_callbacks("Ambilight effect started")

    def stop_ambilight_effect(self):
        """Stop Ambilight (Screen Sync) effect"""
        if self.ambilight_processor:
            self.ambilight_processor.stop()
        self.ambilight_running = False
        if self.active_effect == "ambilight":
            self.active_effect = "static"
        self._notify_status_callbacks("Ambilight effect stopped")

    def _on_ambilight_color(self, r, g, b):
        """Callback for ambilight color updates"""
        if not self.ambilight_running:
            return
            
        # Apply global brightness
        v = self.color_brightness / 1000.0
        # Cast to int immediately
        r_out, g_out, b_out = int(r * v), int(g * v), int(b * v)
        
        self.device_manager.set_color(r_out, g_out, b_out)
        
        hex_color = '#{:02x}{:02x}{:02x}'.format(int(max(0, min(255, r_out))), 
                                                 int(max(0, min(255, g_out))), 
                                                 int(max(0, min(255, b_out))))
        self._notify_color_callbacks(hex_color)

    def set_ambilight_parameters(self, alpha: Optional[float] = None, monitor_index: Optional[int] = None, mode: Optional[str] = None, crop_percent: Optional[int] = None):
        """Set ambilight effect parameters"""
        if self.ambilight_processor:
            if alpha is not None:
                self.ambilight_processor.alpha = alpha
            if monitor_index is not None:
                self.ambilight_processor.monitor_index = monitor_index
            if mode is not None:
                self.ambilight_processor.mode = mode
            if crop_percent is not None:
                self.ambilight_processor.crop_percent = crop_percent
    
    def start_smart_ambient_effect(self):
        """Start Smart Ambient effect - automatically picks best colors"""
        if self.smart_ambient_running:
            return True
        
        # Stop other effects first
        self.stop_all_effects()
        
        success = self.smart_ambient_processor.start(
            color_callback=self._on_smart_ambient_color,
            status_callback=self._on_smart_ambient_status
        )
        
        if success:
            self.smart_ambient_running = True
            self.active_effect = "smart_ambient"
            self._smart_last_send_ts = 0.0
            self._notify_status_callbacks("Smart ambient effect started")
            return True
        else:
            self._notify_status_callbacks("Failed to start smart ambient effect")
            return False
    
    def stop_smart_ambient_effect(self):
        """Stop Smart Ambient effect"""
        if self.smart_ambient_processor:
            self.smart_ambient_processor.stop()
        
        self.smart_ambient_running = False
        if self.active_effect == "smart_ambient":
            self.active_effect = "static"
        
        self._notify_status_callbacks("Smart ambient effect stopped")
    
    def _on_smart_ambient_color(self, hex_color: str):
        """Callback for smart ambient color updates"""
        if not self.smart_ambient_running:
            return
        
        try:
            # Throttle send rate if configured
            now_ts = time.time()
            if self.smart_send_rate_limit > 0.0 and (now_ts - self._smart_last_send_ts) < self.smart_send_rate_limit:
                return
            # Convert hex to RGB
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            
            # Send to device
            self.device_manager.set_color(r, g, b)
            self._smart_last_send_ts = now_ts
            
            # Notify callbacks
            self._notify_color_callbacks(hex_color)
            
        except Exception as e:
            logging.getLogger(__name__).error(f"Smart ambient color error: {e}")
    
    def _on_smart_ambient_status(self, status: str):
        """Callback for smart ambient status updates"""
        self._notify_status_callbacks(status)
    
    def set_smart_ambient_parameters(self, monitor_index: Optional[int] = None, update_interval: Optional[float] = None, send_rate_limit: Optional[float] = None):
        """Set smart ambient effect parameters"""
        if self.smart_ambient_processor:
            if monitor_index is not None:
                self.smart_ambient_processor.set_monitor(monitor_index)
            if update_interval is not None:
                self.smart_ambient_processor.set_update_interval(update_interval)
        if send_rate_limit is not None:
            # Store locally for throttling
            self.smart_send_rate_limit = max(0.0, min(5.0, float(send_rate_limit)))
    
    def set_audio_parameters(self, mode: str, sensitivity: float, brightness: int):
        """Set audio effect parameters"""
        self.audio_mode = mode
        self.beat_sensitivity = sensitivity
        self.color_brightness = brightness
    
    def stop_all_effects(self):
        """Stop all active effects"""
        self.stop_rainbow_effect()
        self.stop_blinker_effect()
        self.stop_strobe_effect()
        self.stop_white_strobe_effect()
        self.stop_ambilight_effect()
        self.stop_smart_ambient_effect()
        self.stop_audio_effect()
        self.active_effect = "static"
        self._notify_status_callbacks("All effects stopped")
    
    def cleanup(self):
        """Cleanup effects engine"""
        self.stop_all_effects()
