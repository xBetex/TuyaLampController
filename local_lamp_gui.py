#!/usr/bin/env python3
"""
Smart Lamp Controller - Enhanced Local Network Version
Controls Tuya-based RGB smart lamps directly via LAN with improved stability and features.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import threading
import time
import colorsys
from queue import Queue, Empty
import tinytuya

# Audio dependencies
try:
    import pyaudio
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# Device Configuration
DEVICE_CONFIG = {
    "name": "Lâmpada NEO 10W RGB",
    "id": "eb3c5109e4834e0442in3u",
    "address": "192.168.15.30",
    "local_key": "IRXcMvDIPu[!V|2-",
    "version": "3.5"
}

# Data Point mappings
DP_POWER = "20"
DP_MODE = "21" 
DP_BRIGHT = "22"
DP_TEMP = "23"

class LocalLampController:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Smart Lamp Controller - {DEVICE_CONFIG['name']}")
        self.root.geometry("520x650")
        
        # Core state
        self.device = None
        self.is_connected = False
        self.running = True
        
        # Thread-safe command queue for device operations
        self.cmd_queue = Queue()
        
        # Effect state tracking
        self.active_effect = "static"
        self.rainbow_running = False
        self.mic_running = False
        self.last_hsv = (0.0, 1.0, 1.0)  # Store last color for brightness adjustments
        
        # UI Variables
        self.status_var = tk.StringVar(value="Initializing...")
        self.brightness_var = tk.DoubleVar(value=500)
        self.temp_var = tk.DoubleVar(value=500)
        self.color_bright_var = tk.DoubleVar(value=1000)
        self.rainbow_speed_var = tk.DoubleVar(value=50)
        self.rainbow_h_min = tk.DoubleVar(value=0.0)
        self.rainbow_h_max = tk.DoubleVar(value=1.0)
        
        # Audio setup
        self.audio_devices = self._get_audio_devices() if AUDIO_AVAILABLE else []
        self.selected_audio_device_index = tk.IntVar(value=self._get_default_input_device_index())
        self.mic_needs_restart = False
        
        self.setup_gui()
        
        # Start background threads
        threading.Thread(target=self._device_worker, daemon=True).start()
        threading.Thread(target=self.connect_to_device, daemon=True).start()
        
        if AUDIO_AVAILABLE:
            threading.Thread(target=self._audio_listener, daemon=True).start()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ================= DEVICE THREAD MANAGEMENT =================
    
    def _device_worker(self):
        """Background worker thread for device commands to prevent UI blocking"""
        while self.running:
            try:
                fn, args, kwargs = self.cmd_queue.get(timeout=0.2)
                fn(*args, **kwargs)
            except Empty:
                pass
            except Exception as e:
                print(f"Device command error: {e}")
    
    def send_command(self, fn, *args, **kwargs):
        """Thread-safe way to send commands to device"""
        if self.is_connected:
            self.cmd_queue.put((fn, args, kwargs))
        else:
            messagebox.showwarning("Connection", "Not connected to lamp!")
    
    def ensure_color_mode(self):
        """Ensure lamp is in color mode for effects"""
        if self.active_effect != "color":
            self.active_effect = "color"
            self.mode_var.set("colour")
            self.send_command(self.device.set_value, DP_MODE, "colour")

    # ================= AUDIO DEVICE MANAGEMENT =================
    
    def _get_audio_devices(self):
        """Get list of available audio input devices"""
        if not AUDIO_AVAILABLE:
            return []
        
        try:
            p = pyaudio.PyAudio()
            devices = []
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    devices.append((i, info.get('name', f'Device {i}')))
            p.terminate()
            return devices
        except Exception as e:
            print(f"Error getting audio devices: {e}")
            return []

    def _get_default_input_device_index(self):
        """Get default audio input device index"""
        if not AUDIO_AVAILABLE:
            return 0
        
        try:
            p = pyaudio.PyAudio()
            idx = p.get_default_input_device_info()['index']
            p.terminate()
            return idx
        except:
            return 0

    # ================= GUI SETUP =================

    def setup_gui(self):
        """Create the main GUI interface"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status Header
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(status_frame, text="Status:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 9))
        status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Power Controls
        power_frame = ttk.LabelFrame(main_frame, text="Power Control", padding="10")
        power_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(power_frame)
        btn_frame.pack(fill=tk.X)
        
        self.btn_on = ttk.Button(btn_frame, text="Turn ON 💡", 
                                command=lambda: self.send_command(self.device.turn_on))
        self.btn_on.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        self.btn_off = ttk.Button(btn_frame, text="Turn OFF 🌑", 
                                 command=lambda: self.send_command(self.device.turn_off))
        self.btn_off.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # Mode Selection
        mode_frame = ttk.LabelFrame(main_frame, text="Light Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        
        self.mode_var = tk.StringVar(value="white")
        mode_btn_frame = ttk.Frame(mode_frame)
        mode_btn_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(mode_btn_frame, text="White Light", variable=self.mode_var, 
                       value="white", command=self.set_mode).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_btn_frame, text="Color Light", variable=self.mode_var, 
                       value="colour", command=self.set_mode).pack(side=tk.LEFT, padx=10)

        # Create notebook for different control tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # White Light Tab
        self.setup_white_tab()
        
        # Color Control Tab
        self.setup_color_tab()
        
        # Effects Tab
        self.setup_effects_tab()
        
        # Audio Reactive Tab
        if AUDIO_AVAILABLE:
            self.setup_audio_tab()

    def setup_white_tab(self):
        """Setup white light controls"""
        white_frame = ttk.Frame(self.notebook)
        self.notebook.add(white_frame, text="White Light")
        
        content = ttk.Frame(white_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Brightness Control
        bright_frame = ttk.LabelFrame(content, text="Brightness", padding="10")
        bright_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(bright_frame, text="Brightness Level").pack(anchor=tk.W)
        self.bright_slider = ttk.Scale(bright_frame, from_=10, to=1000, 
                                      variable=self.brightness_var, orient=tk.HORIZONTAL)
        self.bright_slider.pack(fill=tk.X, pady=(5, 0))
        self.bright_slider.bind("<ButtonRelease-1>", self.on_brightness_change)
        
        bright_val_frame = ttk.Frame(bright_frame)
        bright_val_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(bright_val_frame, text="10").pack(side=tk.LEFT)
        ttk.Label(bright_val_frame, text="1000").pack(side=tk.RIGHT)
        
        # Temperature Control
        temp_frame = ttk.LabelFrame(content, text="Color Temperature", padding="10")
        temp_frame.pack(fill=tk.X)
        
        ttk.Label(temp_frame, text="Temperature (Warm ← → Cool)").pack(anchor=tk.W)
        self.temp_slider = ttk.Scale(temp_frame, from_=0, to=1000, 
                                    variable=self.temp_var, orient=tk.HORIZONTAL)
        self.temp_slider.pack(fill=tk.X, pady=(5, 0))
        self.temp_slider.bind("<ButtonRelease-1>", self.on_temp_change)
        
        temp_val_frame = ttk.Frame(temp_frame)
        temp_val_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(temp_val_frame, text="Warm").pack(side=tk.LEFT)
        ttk.Label(temp_val_frame, text="Cool").pack(side=tk.RIGHT)

    def setup_color_tab(self):
        """Setup color controls"""
        color_frame = ttk.Frame(self.notebook)
        self.notebook.add(color_frame, text="Static Color")
        
        content = ttk.Frame(color_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Color Intensity
        intensity_frame = ttk.LabelFrame(content, text="Color Intensity", padding="10")
        intensity_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(intensity_frame, text="Brightness Level").pack(anchor=tk.W)
        self.color_bright_slider = ttk.Scale(intensity_frame, from_=10, to=1000, 
                                           variable=self.color_bright_var, orient=tk.HORIZONTAL)
        self.color_bright_slider.pack(fill=tk.X, pady=(5, 0))
        self.color_bright_slider.bind("<ButtonRelease-1>", self.on_color_brightness_change)
        
        # Color Selection
        picker_frame = ttk.LabelFrame(content, text="Color Selection", padding="10")
        picker_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(picker_frame, text="Choose Color 🎨", 
                  command=self.choose_color).pack(fill=tk.X, pady=(0, 10))
        
        # Color Preview
        self.color_preview = tk.Label(picker_frame, text="Current Color", 
                                     bg="#888888", height=3, relief="sunken")
        self.color_preview.pack(fill=tk.X)

    def setup_effects_tab(self):
        """Setup effects controls"""
        effects_frame = ttk.Frame(self.notebook)
        self.notebook.add(effects_frame, text="Effects")
        
        content = ttk.Frame(effects_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Rainbow Effect
        rainbow_frame = ttk.LabelFrame(content, text="Rainbow Effect", padding="10")
        rainbow_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Speed Control
        ttk.Label(rainbow_frame, text="Animation Speed").pack(anchor=tk.W)
        speed_frame = ttk.Frame(rainbow_frame)
        speed_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Scale(speed_frame, from_=1, to=100, variable=self.rainbow_speed_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        speed_val_frame = ttk.Frame(speed_frame)
        speed_val_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(speed_val_frame, text="Slow").pack(side=tk.LEFT)
        ttk.Label(speed_val_frame, text="Fast").pack(side=tk.RIGHT)
        
        # Color Range
        range_frame = ttk.Frame(rainbow_frame)
        range_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(range_frame, text="Color Range - Start Hue").pack(anchor=tk.W)
        self.hue_min_scale = ttk.Scale(range_frame, from_=0.0, to=1.0, 
                                      variable=self.rainbow_h_min, orient=tk.HORIZONTAL)
        self.hue_min_scale.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(range_frame, text="Color Range - End Hue").pack(anchor=tk.W)
        self.hue_max_scale = ttk.Scale(range_frame, from_=0.0, to=1.0, 
                                      variable=self.rainbow_h_max, orient=tk.HORIZONTAL)
        self.hue_max_scale.pack(fill=tk.X)
        
        # Rainbow Control Button
        self.rainbow_btn = ttk.Button(rainbow_frame, text="Start Rainbow 🌈", 
                                     command=self.toggle_rainbow)
        self.rainbow_btn.pack(fill=tk.X, pady=(10, 0))

    def setup_audio_tab(self):
        """Setup audio reactive controls"""
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="Music Sync")
        
        content = ttk.Frame(audio_frame, padding="15")
        content.pack(fill=tk.BOTH, expand=True)
        
        # Device Selection
        device_frame = ttk.LabelFrame(content, text="Audio Input Device", padding="10")
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(device_frame, text="Select Input Device:").pack(anchor=tk.W, pady=(0, 5))
        
        if self.audio_devices:
            dev_names = [d[1] for d in self.audio_devices]
            dev_ids = [d[0] for d in self.audio_devices]
            
            self.device_combo = ttk.Combobox(device_frame, values=dev_names, state="readonly")
            self.device_combo.pack(fill=tk.X, pady=(0, 5))
            
            try:
                default_idx = self.selected_audio_device_index.get()
                list_pos = next((i for i, v in enumerate(dev_ids) if v == default_idx), 0)
                self.device_combo.current(list_pos)
            except:
                self.device_combo.current(0)
            
            self.device_combo.bind("<<ComboboxSelected>>", self.on_audio_device_change)
        else:
            ttk.Label(device_frame, text="No audio devices found").pack()
        
        # Music Sync Control
        sync_frame = ttk.LabelFrame(content, text="Music Synchronization", padding="10")
        sync_frame.pack(fill=tk.X)
        
        ttk.Label(sync_frame, text="Lamp will react to music and sound in real-time").pack(pady=(0, 10))
        
        self.mic_btn = ttk.Button(sync_frame, text="Start Music Sync 🎤", 
                                 command=self.toggle_mic_mode)
        self.mic_btn.pack(fill=tk.X)

    # ================= EVENT HANDLERS =================
    
    def on_audio_device_change(self, event):
        """Handle audio device selection change"""
        sel_idx = self.device_combo.current()
        if sel_idx >= 0:
            dev_id = self.audio_devices[sel_idx][0]
            self.selected_audio_device_index.set(dev_id)
            self.mic_needs_restart = True
            print(f"Audio device changed to: {self.audio_devices[sel_idx][1]}")

    def on_brightness_change(self, event):
        """Handle white brightness change"""
        if not self.is_connected:
            return
        val = int(self.brightness_var.get())
        self.send_command(self.device.set_value, DP_BRIGHT, val)

    def on_temp_change(self, event):
        """Handle color temperature change"""
        if not self.is_connected:
            return
        val = int(self.temp_var.get())
        self.send_command(self.device.set_value, DP_TEMP, val)

    def on_color_brightness_change(self, event):
        """Handle color brightness change"""
        if self.active_effect == "color" and self.last_hsv:
            self.apply_color_brightness()

    # ================= DEVICE CONTROL =================
    
    def set_mode(self):
        """Set lamp mode (white/color)"""
        if not self.is_connected:
            return
        mode = self.mode_var.get()
        self.send_command(self.device.set_value, DP_MODE, mode)
        
        # Stop effects when switching modes
        if hasattr(self, 'rainbow_running') and self.rainbow_running:
            self.toggle_rainbow()
        if self.mic_running:
            self.toggle_mic_mode()

    def choose_color(self):
        """Open color picker and set lamp color"""
        if not self.is_connected:
            return
        
        color = colorchooser.askcolor(title="Choose Lamp Color")
        if not color[1]:  # User cancelled
            return
            
        rgb = color[0]  # (r, g, b) tuple
        hex_col = color[1]  # hex string
        
        # Convert to HSV and store
        r, g, b = [x/255.0 for x in rgb]
        h, s, _ = colorsys.rgb_to_hsv(r, g, b)
        v = self.color_bright_var.get() / 1000.0
        self.last_hsv = (h, s, v)
        
        # Switch to color mode and apply
        self.ensure_color_mode()
        
        # Apply color with current brightness
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.send_command(self.device.set_colour, r*255, g*255, b*255)
        
        # Update preview
        final_hex = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
        self.color_preview.config(bg=final_hex)
        
        print(f"Color set: H:{h:.2f} S:{s:.2f} V:{v:.2f}")

    def apply_color_brightness(self):
        """Apply brightness change to current color"""
        if not self.last_hsv or self.active_effect != "color":
            return
            
        h, s, _ = self.last_hsv
        v = self.color_bright_var.get() / 1000.0
        self.last_hsv = (h, s, v)
        
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.send_command(self.device.set_colour, r*255, g*255, b*255)
        
        # Update preview
        hex_col = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
        self.color_preview.config(bg=hex_col)

    # ================= RAINBOW EFFECT =================
    
    def toggle_rainbow(self):
        """Start/stop rainbow effect"""
        if not self.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if hasattr(self, 'rainbow_running') and self.rainbow_running:
            self.rainbow_running = False
            self.rainbow_btn.config(text="Start Rainbow 🌈")
            self.active_effect = "static"
            return

        # Stop other effects
        if self.mic_running:
            self.toggle_mic_mode()
            
        # Start rainbow
        self.rainbow_running = True
        self.rainbow_btn.config(text="Stop Rainbow 🛑")
        self.active_effect = "rainbow"
        
        # Ensure color mode
        self.ensure_color_mode()
        
        threading.Thread(target=self._rainbow_loop, daemon=True).start()

    def _rainbow_loop(self):
        """Rainbow effect main loop"""
        hue = self.rainbow_h_min.get()
        
        while self.running and getattr(self, 'rainbow_running', False):
            try:
                # Speed control (1-100 -> delay calculation)
                speed = self.rainbow_speed_var.get()
                delay = max(0.01, 0.2 - (speed / 600.0))
                
                # Hue progression
                h_min = self.rainbow_h_min.get()
                h_max = self.rainbow_h_max.get()
                
                # Ensure valid range
                if h_min >= h_max:
                    h_max = h_min + 0.1
                
                hue += 0.005
                if hue > h_max:
                    hue = h_min
                
                # Apply color
                v = self.color_bright_var.get() / 1000.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                
                self.send_command(self.device.set_colour, r*255, g*255, b*255)
                
                # Update preview
                hex_col = '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
                self.root.after(0, lambda c=hex_col: self.color_preview.config(bg=c))
                
                time.sleep(delay)
                
            except Exception as e:
                print(f"Rainbow loop error: {e}")
                break

    # ================= AUDIO REACTIVE =================
    
    def toggle_mic_mode(self):
        """Start/stop music sync mode"""
        if not self.is_connected:
            messagebox.showwarning("Connection", "Not connected to lamp!")
            return
        
        if not AUDIO_AVAILABLE:
            messagebox.showerror("Audio Error", "PyAudio not available. Install with: pip install pyaudio")
            return
        
        if self.mic_running:
            self.mic_running = False
            self.mic_btn.config(text="Start Music Sync 🎤")
            self.active_effect = "static"
        else:
            # Stop other effects
            if hasattr(self, 'rainbow_running') and self.rainbow_running:
                self.toggle_rainbow()
            
            self.mic_running = True
            self.mic_btn.config(text="Stop Music Sync 🛑")
            self.active_effect = "music"
            
            # Ensure color mode
            self.ensure_color_mode()
            
            print("Music sync started")

    def _audio_listener(self):
        """Audio processing thread for music sync"""
        if not AUDIO_AVAILABLE:
            return
        
        p = pyaudio.PyAudio()
        stream = None
        current_dev = self.selected_audio_device_index.get()
        
        # Initialize audio stream
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                input=True,
                input_device_index=current_dev,
                frames_per_buffer=1024
            )
            print(f"Audio stream initialized on device {current_dev}")
        except Exception as e:
            print(f"Audio init failed: {e}. Trying default device.")
            try:
                stream = p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=44100,
                    input=True,
                    frames_per_buffer=1024
                )
            except Exception as e2:
                print(f"Default audio init failed: {e2}")
                return
        
        # Audio processing variables
        hue = 0.0
        noise_floor = 100.0
        last_beat = 0
        
        print("Audio listener started")
        
        while self.running:
            # Handle device restart
            if getattr(self, 'mic_needs_restart', False):
                print("Restarting audio stream...")
                try:
                    if stream:
                        stream.stop_stream()
                        stream.close()
                except:
                    pass
                
                current_dev = self.selected_audio_device_index.get()
                try:
                    stream = p.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=44100,
                        input=True,
                        input_device_index=current_dev,
                        frames_per_buffer=1024
                    )
                    print(f"Switched to device index {current_dev}")
                except Exception as e:
                    print(f"Error switching device: {e}")
                
                self.mic_needs_restart = False
            
            # Process audio when mic mode is active
            if self.mic_running and self.is_connected and stream:
                try:
                    # Read audio data
                    data = np.frombuffer(
                        stream.read(1024, exception_on_overflow=False), 
                        dtype=np.int16
                    )
                    
                    # Calculate RMS (volume level)
                    rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))
                    
                    # Adaptive noise floor
                    noise_floor = 0.95 * noise_floor + 0.05 * rms
                    
                    # React to sound above noise floor
                    if rms > noise_floor * 1.5:
                        now = time.time()
                        
                        # Beat detection - significant volume increase
                        if rms > noise_floor * 3.0 and (now - last_beat) > 0.1:
                            last_beat = now
                            hue = (hue + 0.15) % 1.0  # Shift color on beat
                        
                        # Volume-based brightness
                        max_bright = self.color_bright_var.get()
                        volume_bright = min(max_bright, max(50, int(rms / 15)))
                        v = volume_bright / 1000.0
                        
                        # Apply color
                        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, v)
                        self.send_command(self.device.set_colour, r*255, g*255, b*255)
                        
                    else:
                        # Fade to dim when quiet
                        time.sleep(0.05)
                        
                except Exception as e:
                    print(f"Audio processing error: {e}")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        
        # Cleanup
        try:
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()
        except:
            pass

    # ================= CONNECTION MANAGEMENT =================
    
    def connect_to_device(self):
        """Connect to the Tuya device"""
        try:
            self.status_var.set(f"Connecting to {DEVICE_CONFIG['address']}...")
            
            self.device = tinytuya.BulbDevice(
                dev_id=DEVICE_CONFIG['id'],
                address=DEVICE_CONFIG['address'],
                local_key=DEVICE_CONFIG['local_key']
            )
            
            # Set device version and enable persistent connection
            self.device.set_version(float(DEVICE_CONFIG['version']))
            self.device.set_socketPersistent(True)
            
            # Test connection
            data = self.device.status()
            if 'Error' in str(data):
                self.status_var.set(f"Connection Error: {data}")
                print(f"Device status error: {data}")
            else:
                self.status_var.set("Connected ✅")
                self.is_connected = True
                self.parse_status(data)
                print("Successfully connected to lamp")
                
        except Exception as e:
            error_msg = f"Connection Failed: {str(e)}"
            self.status_var.set(error_msg)
            print(error_msg)

    def parse_status(self, data):
        """Parse device status and update UI"""
        if not data or 'dps' not in data:
            return
            
        try:
            dps = data['dps']
            print(f"Device status: {dps}")
            
            # Update mode
            if DP_MODE in dps:
                self.mode_var.set(dps[DP_MODE])
                
            # Update brightness
            if DP_BRIGHT in dps:
                self.brightness_var.set(dps[DP_BRIGHT])
                
            # Update temperature
            if DP_TEMP in dps:
                self.temp_var.set(dps[DP_TEMP])
                
        except Exception as e:
            print(f"Error parsing status: {e}")

    # ================= CLEANUP =================
    
    def on_close(self):
        """Handle application close"""
        print("Shutting down...")
        self.running = False
        
        # Stop effects
        if hasattr(self, 'rainbow_running'):
            self.rainbow_running = False
        self.mic_running = False
        
        # Close device connection
        if self.device:
            try:
                self.device.close()
            except:
                pass
        
        self.root.destroy()


def main():
    """Main application entry point"""
    root = tk.Tk()
    
    # Set application icon and style
    try:
        root.iconbitmap(default='lamp.ico')  # Add if you have an icon file
    except:
        pass
    
    # Create and run application
    app = LocalLampController(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_close()


if __name__ == "__main__":
    main()