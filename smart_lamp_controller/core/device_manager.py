"""
Device communication manager for Smart Lamp Controller
"""
import threading
import time
import logging
import os
from queue import Queue, Empty
from typing import Optional, Callable, Dict, Any
import tinytuya

class DeviceManager:
    """Manages communication with Tuya smart lamp device"""
    
    def __init__(self, device_config: Dict[str, Any], data_points: Dict[str, str]):
        self.device_config = device_config
        self.data_points = data_points
        self.device: Optional[tinytuya.BulbDevice] = None
        self.is_connected = False
        self.running = True
        
        # Thread-safe command queue with conflation support
        self._cmd_list = []
        self.queue_lock = threading.Lock()
        self.queue_condition = threading.Condition(self.queue_lock)
        
        # Callbacks for status updates
        self.status_callbacks = []
        self.connection_callbacks = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Start device worker thread
        self.worker_thread = threading.Thread(target=self._device_worker, daemon=True)
        self.worker_thread.start()
    
    def add_status_callback(self, callback: Callable[[str], None]):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    def add_connection_callback(self, callback: Callable[[bool], None]):
        """Add callback for connection state changes"""
        self.connection_callbacks.append(callback)
    
    def _notify_status(self, status: str):
        """Notify all status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(status)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    def _notify_connection(self, connected: bool):
        """Notify all connection callbacks"""
        self.is_connected = connected
        for callback in self.connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                self.logger.error(f"Connection callback error: {e}")
    
    def _device_worker(self):
        """Worker thread for processing device commands"""
        consecutive_failures = 0
        MAX_FAILURES = 3

        while self.running:
            try:
                with self.queue_lock:
                    while not self._cmd_list and self.running:
                        if not self.queue_condition.wait(timeout=0.2):
                            break

                    if not self._cmd_list or not self.running:
                        continue

                    cmd_data = self._cmd_list.pop(0)

                fn = cmd_data['fn']
                args = cmd_data['args']
                kwargs = cmd_data['kwargs']

                if self.is_connected and self.device:
                    try:
                        fn(*args, **kwargs)
                        consecutive_failures = 0
                        # Minimal delay after high-frequency commands
                        if cmd_data.get('conflate_key'):
                            time.sleep(0.015)
                    except Exception as e:
                        consecutive_failures += 1
                        self.logger.error(f"Device execution error ({consecutive_failures}/{MAX_FAILURES}): {e}")

                        if consecutive_failures >= MAX_FAILURES:
                            self.logger.warning("Connection lost — too many consecutive failures, reconnecting...")
                            self._notify_status("Connection lost — reconnecting...")
                            self._notify_connection(False)

                            # Flush stale commands that would also fail
                            with self.queue_lock:
                                self._cmd_list.clear()

                            # Attempt to re-establish the socket
                            if self._try_reconnect_socket():
                                consecutive_failures = 0

            except Exception as e:
                self.logger.error(f"Device worker error: {e}")
                time.sleep(0.1)

    def _try_reconnect_socket(self) -> bool:
        """Attempt to silently re-establish the device socket. Returns True on success."""
        try:
            if self.device:
                try:
                    self.device.close()
                except Exception:
                    pass

            time.sleep(1)

            self.device = tinytuya.BulbDevice(
                dev_id=self.device_config['id'],
                address=self.device_config['address'],
                local_key=self.device_config['local_key']
            )
            self.device.set_version(float(self.device_config['version']))
            self.device.set_socketTimeout(5)
            self.device.set_socketPersistent(True)

            data = self.device.status()
            if data and 'Error' not in str(data):
                self._notify_connection(True)
                self._notify_status("Reconnected ✅")
                self.logger.info("Socket reconnected successfully")
                return True
            else:
                self._notify_status(f"Reconnect failed: {data}")
                self.logger.error(f"Reconnect status check failed: {data}")
                return False

        except Exception as e:
            self.logger.error(f"Socket reconnect failed: {e}")
            self._notify_status(f"Reconnect failed: {e}")
            return False
    
    def send_command(self, fn: Callable, *args, urgent: bool = False, **kwargs):
        """Queue a command for execution with conflation and priority support"""
        if not self.is_connected:
            self.logger.warning("Device not connected - command ignored")
            return

        if not self.device:
            return

        conflate_key = None
        if fn == self.device.set_colour:
            conflate_key = "set_colour"
        elif fn == self.device.set_value:
            if args:
                conflate_key = f"set_value_{args[0]}"
        
        with self.queue_lock:
            # If a conflate_key is provided, remove existing commands with the same key
            if conflate_key:
                self._cmd_list = [cmd for cmd in self._cmd_list if cmd.get('conflate_key') != conflate_key]
            
            # Priority Handling
            if urgent:
                # If urgent, we often want to clear the queue (e.g. Turn OFF should stop color updates)
                if fn == self.device.turn_off:
                    # Clear all pending color/value updates when turning off
                    self._cmd_list = [cmd for cmd in self._cmd_list if cmd.get('conflate_key') is None]
                
                # Insert at front of queue
                self._cmd_list.insert(0, {
                    'fn': fn,
                    'args': args,
                    'kwargs': kwargs,
                    'conflate_key': conflate_key,
                    'urgent': True
                })
            else:
                # Standard append
                self._cmd_list.append({
                    'fn': fn,
                    'args': args,
                    'kwargs': kwargs,
                    'conflate_key': conflate_key
                })
            
            # Limit total queue size
            if len(self._cmd_list) > 100:
                self._cmd_list = self._cmd_list[-50:]
                self.logger.warning(f"Queue overflow! Dropped commands. New size: {len(self._cmd_list)}")

            # Fire-and-forget for all high-freq conflated commands (including set_colour)
            if conflate_key and 'nowait' not in kwargs:
                kwargs['nowait'] = True
                
            self.queue_condition.notify()
    
    def connect(self) -> bool:
        """Connect to the device"""
        try:
            self._notify_status(f"Connecting to {self.device_config['address']}...")
            
            # Try with current local key first
            self.device = tinytuya.BulbDevice(
                dev_id=self.device_config['id'],
                address=self.device_config['address'],
                local_key=self.device_config['local_key']
            )
            
            self.device.set_version(float(self.device_config['version']))
            self.device.set_socketTimeout(5)
            self.device.set_socketPersistent(True)

            # Test connection with retry (first attempt may timeout during session negotiation)
            data = None
            for attempt in range(3):
                data = self.device.status()
                if data and 'Error' not in str(data):
                    break
                self.logger.info(f"Connection attempt {attempt + 1} returned: {data}")
                if attempt < 2:
                    import time as _t
                    _t.sleep(1)

            if 'Error' in str(data):
                self._notify_status(f"Connection failed with current key, trying re-pairing...")
                self.logger.warning("Current local key failed, attempting key refresh...")
                
                # Try to refresh the key by connecting with empty key
                try:
                    self.device = tinytuya.BulbDevice(
                        dev_id=self.device_config['id'],
                        address=self.device_config['address'],
                        local_key=""  # Empty key to trigger re-pairing
                    )
                    
                    self.device.set_version(float(self.device_config['version']))
                    self.device.set_socketPersistent(True)
                    
                    # Test connection - this should generate a new key
                    data = self.device.status()
                    
                    if 'Error' not in str(data):
                        # Update the local key in device config
                        new_key = self.device.local_key
                        self.device_config['local_key'] = new_key
                        
                        # Save updated config
                        try:
                            import json
                            config_path = os.path.join(os.path.dirname(__file__), '..', 'lamp_config.json')
                            with open(config_path, 'r') as f:
                                config = json.load(f)
                            config['device']['local_key'] = new_key
                            with open(config_path, 'w') as f:
                                json.dump(config, f, indent=2, ensure_ascii=False)
                            
                            self._notify_status(f"✅ Key refreshed: {new_key}")
                            self.logger.info(f"Local key updated to: {new_key}")
                        except Exception as e:
                            self.logger.error(f"Failed to save updated key: {e}")
                        
                    else:
                        self._notify_status(f"Re-pairing failed: {data}")
                        self._notify_connection(False)
                        return False
                        
                except Exception as e:
                    self.logger.error(f"Key refresh failed: {e}")
                    self._notify_status(f"Key refresh failed: {str(e)}")
                    self._notify_connection(False)
                    return False
            
            # Final connection test
            data = self.device.status()
            if 'Error' in str(data):
                self._notify_status(f"Connection Error: {data}")
                self._notify_connection(False)
                return False
            else:
                self._notify_status("Connected ✅")
                self._notify_connection(True)
                self._parse_and_notify_status(data)
                return True
                
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self._notify_status(f"Connection Failed: {str(e)}")
            self._notify_connection(False)
            return False
    
    def disconnect(self):
        """Disconnect from the device without shutting down the worker"""
        try:
            if self.device:
                self.device.close()
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
        finally:
            self._notify_status("Disconnected ❌")
            self._notify_connection(False)

    def check_connection(self) -> bool:
        """Ping the device status to verify connection"""
        try:
            if not self.device:
                self._notify_status("Not connected")
                self._notify_connection(False)
                return False
            data = self.device.status()
            if 'Error' in str(data) or not data:
                self._notify_status("Connection lost ❌")
                self._notify_connection(False)
                return False
            self._parse_and_notify_status(data)
            self._notify_status("Connected ✅")
            self._notify_connection(True)
            return True
        except Exception as e:
            self.logger.error(f"Check connection failed: {e}")
            self._notify_status("Connection check failed")
            self._notify_connection(False)
            return False

    def get_queue_size(self) -> int:
        """Get the current number of pending commands"""
        with self.queue_lock:
            return len(self._cmd_list)

    def reconnect(self) -> bool:
        """Attempt to disconnect and reconnect to the device"""
        # Clear command queue to prevent stuck commands
        with self.queue_lock:
            self._cmd_list = []
                
        self.disconnect()
        time.sleep(0.5)  # Increased wait time for socket cleanup
        return self.connect()

    def _parse_and_notify_status(self, data: Dict[str, Any]):
        """Parse device status and notify callbacks"""
        if not data or 'dps' not in data:
            return
        
        try:
            dps = data['dps']
            status_updates = {}
            
            if self.data_points.get('mode') in dps:
                status_updates['mode'] = dps[self.data_points['mode']]
            if self.data_points.get('brightness') in dps:
                status_updates['brightness'] = dps[self.data_points['brightness']]
            if self.data_points.get('temperature') in dps:
                status_updates['temperature'] = dps[self.data_points['temperature']]
            
            # Notify status callbacks with parsed data
            for callback in self.status_callbacks:
                if hasattr(callback, '__name__') and 'status' in callback.__name__:
                    try:
                        callback(status_updates)
                    except Exception as e:
                        self.logger.error(f"Status update callback error: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error parsing status: {e}")
    
    def turn_on(self):
        """Turn the lamp on with high priority"""
        self.send_command(self.device.turn_on, urgent=True)
    
    def turn_off(self):
        """Turn the lamp off with high priority"""
        self.send_command(self.device.turn_off, urgent=True)
    
    def set_mode(self, mode: str):
        """Set the lamp mode"""
        dp_mode = self.data_points.get('mode')
        if dp_mode:
            self.send_command(self.device.set_value, dp_mode, mode)
    
    def set_brightness(self, brightness: int):
        """Set brightness (10-1000)"""
        dp_bright = self.data_points.get('brightness')
        if dp_bright:
            self.send_command(self.device.set_value, dp_bright, brightness)
    
    def set_temperature(self, temperature: int):
        """Set color temperature (0-1000)"""
        dp_temp = self.data_points.get('temperature')
        if dp_temp:
            self.send_command(self.device.set_value, dp_temp, temperature)
            
    def set_scene(self, scene_data: str):
        """Set lamp to scene mode with specific scene string"""
        dp_mode = self.data_points.get('mode')
        dp_scene = self.data_points.get('scene', '25')
        if dp_mode and dp_scene:
            # First set to scene mode
            self.send_command(self.device.set_value, dp_mode, 'scene')
            # Then set the scene string
            self.send_command(self.device.set_value, dp_scene, scene_data)
            
    def set_white(self, brightness: int, temp: int):
        """Set white light with brightness and temperature (0-1000)"""
        self.send_command(self.device.set_white, brightness, temp)
    
    def set_color(self, r: float, g: float, b: float):
        """Set RGB color (0-255 each)"""
        # Ensure integers for safe transport
        ir, ig, ib = int(r), int(g), int(b)
        self.send_command(self.device.set_colour, ir, ig, ib)
    
    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current device status"""
        if self.is_connected and self.device:
            try:
                return self.device.status()
            except Exception as e:
                self.logger.error(f"Error getting status: {e}")
        return None
    
    def close(self):
        """Close device connection and cleanup"""
        self.running = False
        if self.device:
            try:
                self.device.close()
            except Exception as e:
                self.logger.error(f"Error closing device: {e}")
        
        # Wait for worker thread to finish
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
