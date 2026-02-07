"""
Audio processing module for Smart Lamp Controller
"""
import threading
import time
import logging
from typing import List, Optional, Callable
import numpy as np

# Audio dependencies
try:
    import pyaudio
    from scipy import signal
    AUDIO_AVAILABLE = True
    SCIPY_AVAILABLE = True
except ImportError:
    try:
        import pyaudio
        SCIPY_AVAILABLE = False
        AUDIO_AVAILABLE = True
    except ImportError:
        AUDIO_AVAILABLE = False
        SCIPY_AVAILABLE = False

class AudioProcessor:
    """Handles audio input processing for music synchronization"""
    
    def __init__(self, audio_config: dict):
        self.audio_config = audio_config
        self.running = False
        self.mic_running = False
        self.mic_needs_restart = False
        
        # Audio devices
        self.audio_devices: List[tuple] = []
        self.selected_device_index: int = 0
        
        # Audio processing state
        self.audio_levels: List[float] = [0.0] * 20
        self.frequency_bands: List[float] = [0.0] * 8
        self.viz_spectrum: List[float] = [0.0] * 32
        self.last_beat_time: float = 0
        self.beat_intervals: List[float] = []
        self.current_bpm: int = 0
        
        # Callbacks
        self.level_callbacks: List[Callable[[List[float]], None]] = []
        self.bpm_callbacks: List[Callable[[int], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize audio devices
        if AUDIO_AVAILABLE:
            self._scan_audio_devices()
    
    def _scan_audio_devices(self):
        """Scan for available audio input devices"""
        try:
            p = pyaudio.PyAudio()
            devices = []
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    devices.append((i, info.get('name', f'Device {i}')))
            p.terminate()
            self.audio_devices = devices
            self.logger.info(f"Found {len(devices)} audio input devices")
        except Exception as e:
            self.logger.error(f"Error scanning audio devices: {e}")
            self.audio_devices = []
    
    def get_default_input_device_index(self) -> int:
        """Get default input device index"""
        if not AUDIO_AVAILABLE:
            return 0
        try:
            p = pyaudio.PyAudio()
            idx = p.get_default_input_device_info()['index']
            p.terminate()
            return idx
        except Exception:
            return 0
    
    def add_level_callback(self, callback: Callable[[List[float]], None]):
        """Add callback for audio level updates"""
        self.level_callbacks.append(callback)
    
    def add_bpm_callback(self, callback: Callable[[int], None]):
        """Add callback for BPM updates"""
        self.bpm_callbacks.append(callback)
    
    def _notify_level_callbacks(self):
        """Notify all level callbacks"""
        for callback in self.level_callbacks:
            try:
                callback(self.audio_levels.copy())
            except Exception as e:
                self.logger.error(f"Level callback error: {e}")
    
    def _notify_bpm_callbacks(self):
        """Notify all BPM callbacks"""
        for callback in self.bpm_callbacks:
            try:
                callback(self.current_bpm)
            except Exception as e:
                self.logger.error(f"BPM callback error: {e}")
    
    def set_device(self, device_index: int):
        """Set the audio input device"""
        self.selected_device_index = device_index
        self.mic_needs_restart = True
    
    def start_listening(self):
        """Start audio processing"""
        if not AUDIO_AVAILABLE:
            self.logger.error("PyAudio not available")
            return False
        
        if self.mic_running:
            return True
        
        self.running = True
        self.mic_running = True
        
        # Start audio processing thread
        self.audio_thread = threading.Thread(target=self._audio_listener, daemon=True)
        self.audio_thread.start()
        
        self.logger.info("Audio processing started")
        return True
    
    def stop_listening(self):
        """Stop audio processing"""
        self.mic_running = False
        self.logger.info("Audio processing stopped")
    
    def _audio_listener(self):
        """Main audio processing loop"""
        if not AUDIO_AVAILABLE:
            return
        
        p = pyaudio.PyAudio()
        stream = None
        
        try:
            # Try to open selected device
            target_device_idx = self.selected_device_index
            
            # Get device capabilities
            try:
                dev_info = p.get_device_info_by_index(target_device_idx)
                # Prefer device's native rate to avoid resampling errors
                rates_to_try = [int(dev_info.get('defaultSampleRate', 44100)), 48000, 44100, 16000]
                # Remove duplicates while preserving order
                rates_to_try = list(dict.fromkeys(rates_to_try))
            except Exception:
                rates_to_try = [44100, 48000]
                
            stream = None
            for rate in rates_to_try:
                try:
                    self.logger.info(f"Attempting to open device {target_device_idx} at {rate}Hz")
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=self.audio_config.get('channels', 1),
                        rate=rate,
                        input=True,
                        input_device_index=target_device_idx,
                        frames_per_buffer=self.audio_config.get('buffer_size', 1024)
                    )
                    # Update config with actual rate being used (important for FFT)
                    self.audio_config['sample_rate'] = rate
                    self.logger.info(f"Successfully opened audio device at {rate}Hz")
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to open at {rate}Hz: {e}")
            
            if stream is None:
                self.logger.error("Failed to open selected device with any sample rate. Trying default system device...")
                # Fallback to default device
                try:
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        frames_per_buffer=1024
                    )
                    self.audio_config['sample_rate'] = 44100
                except Exception as e:
                    self.logger.error(f"FATAL: Could not open even default device: {e}")
                    return
            
            # Audio processing state
            noise_floor = 100.0
            last_beat = 0.0
            hue = 0.0
            
            while self.running:
                # Handle device changes
                if self.mic_needs_restart:
                    self._restart_stream(p, stream)
                    stream = None  # Will be recreated in the next iteration
                    self.mic_needs_restart = False
                    continue
                
                if self.mic_running and stream:
                    try:
                        # Read audio data
                        data = np.frombuffer(
                            stream.read(1024, exception_on_overflow=False), 
                            dtype=np.int16
                        )
                        
                        # Calculate RMS
                        rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
                        
                        # Update noise floor (adaptive) - slow adaptation
                        noise_floor = 0.98 * noise_floor + 0.02 * rms
                        
                        # Update visualization levels
                        # More sensitive normalization: headroom is smaller (2x instead of 5x)
                        # This allows visualization/effects to work even with lower delta from noise floor
                        normalized = min(1.0, max(0.0, (rms - noise_floor) / max(1e-6, noise_floor * 2)))
                        self.audio_levels.pop(0)
                        self.audio_levels.append(normalized)
                        
                        # Notify level callbacks
                        self._notify_level_callbacks()
                        
                        # Internal Beat detection (for BPM)
                        # Require signal to be significantly above noise floor and above a minimum absolute threshold
                        if rms > noise_floor * 1.5 and normalized > 0.1:
                            current_time = time.time()
                            if current_time - last_beat > 0.25:  # Cap at ~240 BPM max to reduce noise triggers
                                last_beat = current_time
                                self._process_beat(current_time)
                        
                        # Frequency analysis if scipy is available
                        if SCIPY_AVAILABLE and len(data) >= 512:
                            self._analyze_frequency_bands(data, noise_floor)
                        # Compute fast spectrum for visualization
                        if len(data) >= 512:
                            self._compute_viz_spectrum(data)
                        
                        # Small delay to prevent excessive CPU usage
                        if rms <= noise_floor * 1.2:
                            time.sleep(0.05)
                            
                    except Exception as e:
                        self.logger.error(f"Audio processing error: {e}")
                        time.sleep(0.1)
                else:
                    time.sleep(0.1)
                    
        except Exception as e:
            self.logger.error(f"Audio listener error: {e}")
        finally:
            # Cleanup
            try:
                if stream:
                    stream.stop_stream()
                    stream.close()
                p.terminate()
            except Exception as e:
                self.logger.error(f"Audio cleanup error: {e}")
    
    def _restart_stream(self, p: pyaudio.PyAudio, old_stream):
        """Restart audio stream with new device"""
        try:
            if old_stream:
                old_stream.stop_stream()
                old_stream.close()
        except Exception as e:
            self.logger.error(f"Error stopping old stream: {e}")
    
    def _process_beat(self, current_time: float):
        """Process detected beat"""
        self.beat_intervals.append(current_time)
        # Keep only beats from last 10 seconds
        self.beat_intervals = [t for t in self.beat_intervals if current_time - t < 10]
        
        # Calculate BPM
        if len(self.beat_intervals) > 1:
            avg_interval = (self.beat_intervals[-1] - self.beat_intervals[0]) / (len(self.beat_intervals) - 1)
            if avg_interval > 0:
                bpm = 60 / avg_interval
                self.current_bpm = int(bpm)
                self._notify_bpm_callbacks()
    
    def _analyze_frequency_bands(self, data: np.ndarray, noise_floor: float):
        """Analyze frequency bands in audio data"""
        try:
            # Perform FFT
            fft = np.fft.fft(data)
            freqs = np.fft.fftfreq(len(fft), 1/self.audio_config.get('sample_rate', 44100))
            magnitude = np.abs(fft)
            
            # Define frequency bands (Hz)
            bands = [
                (20, 60),      # Sub-bass
                (60, 250),     # Bass
                (250, 500),    # Low-mid
                (500, 2000),   # Mid
                (2000, 4000),  # High-mid
                (4000, 6000),  # Presence
                (6000, 12000), # Brilliance
                (12000, 20000) # Ultra-high
            ]
            
            # Calculate energy in each band
            band_energies = []
            for low, high in bands:
                mask = (freqs >= low) & (freqs <= high)
                energy = np.sum(magnitude[mask])
                band_energies.append(energy)
            
            self.frequency_bands = band_energies
            
        except Exception as e:
            self.logger.error(f"Frequency analysis error: {e}")
    
    def _compute_viz_spectrum(self, data: np.ndarray):
        """Compute a responsive FFT spectrum for visualization (log-spaced bins)."""
        try:
            n = len(data)
            window = np.hanning(n).astype(np.float32)
            y = data.astype(np.float32) * window
            fft = np.fft.rfft(y)
            mag = np.abs(fft)
            freqs = np.fft.rfftfreq(n, 1 / self.audio_config.get('sample_rate', 44100))

            bins = 32
            f_min, f_max = 50.0, 16000.0
            edges = np.geomspace(f_min, f_max, bins + 1)
            out = []
            for i in range(bins):
                low, high = edges[i], edges[i + 1]
                mask = (freqs >= low) & (freqs < high)
                energy = float(np.sum(mag[mask]))
                out.append(energy)

            arr = np.array(out, dtype=np.float32)
            med = max(1e-6, float(np.median(arr)))
            norm = np.clip(arr / (med * 8.0), 0.0, 1.0)

            if not hasattr(self, '_viz_spec_state') or len(self._viz_spec_state) != bins:
                self._viz_spec_state = np.zeros(bins, dtype=np.float32)
            prev = self._viz_spec_state
            attack = 0.6
            release = 0.2
            higher = norm > prev
            prev[higher] = attack * norm[higher] + (1 - attack) * prev[higher]
            prev[~higher] = release * norm[~higher] + (1 - release) * prev[~higher]
            self._viz_spec_state = prev
            self.viz_spectrum = prev.tolist()
        except Exception as e:
            self.logger.error(f"Viz spectrum error: {e}")
    
    def get_audio_mode_data(self, mode: str, beat_sensitivity: float = 2.5) -> dict:
        """Get processed audio data for specific mode"""
        if not self.mic_running:
            return {}
        
        data = {
            'levels': self.audio_levels.copy(),
            'frequency_bands': self.frequency_bands.copy(),
            'bpm': self.current_bpm,
            'beat_detected': False
        }
        
        if self.audio_levels:
            gain = max(0.5, min(3.0, 0.8 + 0.4 * beat_sensitivity))
            adj_levels = [min(1.0, l * gain) for l in data['levels']]
            data['levels'] = adj_levels
        
        if mode in ['beat_color', 'rms_both', 'beat_white_flash']:
            if len(data['levels']) > 1:
                # Improved beat detection logic for effects
                # Use a dynamic threshold based on recent history to find peaks
                recent_max = max(data['levels'][-5:]) if data['levels'] else 0
                recent_avg = sum(data['levels'][-10:]) / 10 if data['levels'] else 0
                
                # Dynamic threshold: Needs to be above average and above absolute floor
                # Sensitivity reduces the required multiplier above average
                multiplier = max(1.1, 1.8 - (0.1 * beat_sensitivity))
                
                if recent_max > (recent_avg * multiplier) and recent_max > 0.05:
                    current_time = time.time()
                    if current_time - self.last_beat_time > 0.2: # Max 5 beats/sec for lights
                        data['beat_detected'] = True
                        self.last_beat_time = current_time
        
        return data

    def restart(self):
        """Request audio service restart"""
        if not AUDIO_AVAILABLE:
            return False
        self.mic_needs_restart = True
        if not self.mic_running:
            return self.start_listening()
        return True
    
    def cleanup(self):
        """Cleanup audio resources"""
        self.running = False
        self.stop_listening()
