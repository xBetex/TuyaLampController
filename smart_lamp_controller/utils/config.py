"""
Configuration management for Smart Lamp Controller
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Manages application configuration with file persistence"""
    
    DEFAULT_CONFIG = {
        "device": {
            "name": "My Smart Lamp",
            "id": "YOUR_DEVICE_ID",
            "address": "YOUR_DEVICE_IP",
            "local_key": "YOUR_LOCAL_KEY",
            "version": "3.5"
        },
        "ui": {
            "window_width": 650,
            "window_height": 750,
            "theme": "default"
        },
        "audio": {
            "sample_rate": 44100,
            "buffer_size": 1024,
            "channels": 1,
            "default_sensitivity": 2.5
        },
        "effects": {
            "rainbow_speed": 50,
            "default_brightness": 500,
            "default_temperature": 500
        },
        "data_points": {
            "power": "20",
            "mode": "21",
            "brightness": "22",
            "temperature": "23",
            "scene": "25"
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self._config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        # Go up from utils/ to the project root
        app_dir = Path(__file__).parent.parent
        return str(app_dir / "lamp_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to handle missing keys
                return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
        
        return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded config with defaults"""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def save(self) -> bool:
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'device.name')"""
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    @property
    def device_config(self) -> Dict[str, Any]:
        """Get device configuration"""
        return self.get('device', {})
    
    @property
    def ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get('ui', {})
    
    @property
    def audio_config(self) -> Dict[str, Any]:
        """Get audio configuration"""
        return self.get('audio', {})
    
    @property
    def effects_config(self) -> Dict[str, Any]:
        """Get effects configuration"""
        return self.get('effects', {})
    
    @property
    def data_points(self) -> Dict[str, str]:
        """Get data point mappings"""
        return self.get('data_points', {})
