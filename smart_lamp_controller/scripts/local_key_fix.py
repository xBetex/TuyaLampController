#!/usr/bin/env python3
"""
Local Key Fix for Smart Lamp Controller
Sets up a persistent local key that doesn't change when lamp is turned off
"""
import json
import logging
import tinytuya
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalKeyManager:
    """Manages persistent local keys for Tuya devices"""
    
    def __init__(self, config_file: str = "lamp_config.json"):
        self.config_file = config_file
        self.backup_file = config_file.replace('.json', '_backup.json')
        
    def load_config(self) -> Dict[str, Any]:
        """Load current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {self.config_file} not found")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}
    
    def backup_config(self):
        """Create backup of current config"""
        try:
            config = self.load_config()
            with open(self.backup_file, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Config backed up to {self.backup_file}")
        except Exception as e:
            logger.error(f"Failed to backup config: {e}")
    
    def save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def generate_persistent_key(self) -> str:
        """Generate a persistent local key"""
        import secrets
        # Generate a 16-character hex key (similar to Tuya format)
        return secrets.token_hex(8).upper()
    
    def set_persistent_key(self, new_key: Optional[str] = None) -> bool:
        """Set a persistent local key for the device"""
        config = self.load_config()
        
        if 'device' not in config:
            logger.error("No device configuration found")
            return False
        
        device_config = config['device']
        
        # Backup current config
        self.backup_config()
        
        # Generate or use provided key
        if new_key is None:
            new_key = self.generate_persistent_key()
            logger.info(f"Generated new persistent key: {new_key}")
        else:
            logger.info(f"Using provided persistent key: {new_key}")
        
        # Update the local key
        old_key = device_config.get('local_key', '')
        device_config['local_key'] = new_key
        
        # Add metadata about the key change
        device_config['_key_metadata'] = {
            'key_type': 'persistent',
            'previous_key': old_key,
            'set_timestamp': __import__('time').time(),
            'note': 'Set by local_key_fix.py to prevent key rotation'
        }
        
        # Save updated config
        self.save_config(config)
        
        logger.info(f"✅ Persistent local key set successfully!")
        logger.info(f"Old key: {old_key}")
        logger.info(f"New key: {new_key}")
        
        return True
    
    def test_connection(self) -> bool:
        """Test connection with current persistent key"""
        config = self.load_config()
        
        if 'device' not in config:
            logger.error("No device configuration found")
            return False
        
        device_config = config['device']
        
        try:
            # Create device instance
            device = tinytuya.BulbDevice(
                dev_id=device_config['id'],
                address=device_config['address'],
                local_key=device_config['local_key']
            )
            
            device.set_version(float(device_config.get('version', '3.5')))
            
            # Test connection
            logger.info("Testing connection with persistent key...")
            data = device.status()
            
            if 'Error' in str(data):
                logger.error(f"Connection test failed: {data}")
                return False
            
            logger.info("✅ Connection test successful!")
            logger.info(f"Device status: {data}")
            return True
            
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False
    
    def force_key_update(self) -> bool:
        """Force the device to accept the new persistent key"""
        logger.info("Attempting to force key update...")
        
        # First, try to connect with empty key to trigger key exchange
        config = self.load_config()
        device_config = config['device']
        
        try:
            # Create device with empty key
            device = tinytuya.BulbDevice(
                dev_id=device_config['id'],
                address=device_config['address'],
                local_key=""  # Empty key to trigger re-pairing
            )
            
            device.set_version(float(device_config.get('version', '3.5')))
            
            # Try to get status - this should trigger key exchange
            logger.info("Attempting re-pairing with empty key...")
            data = device.status()
            
            if 'Error' not in str(data):
                # If successful, the device should have generated a new key
                new_key = device.local_key
                logger.info(f"Device generated new key: {new_key}")
                
                # Now update our config with this key
                device_config['local_key'] = new_key
                self.save_config(config)
                
                logger.info("✅ Key updated successfully!")
                return True
            else:
                logger.error(f"Re-pairing failed: {data}")
                return False
                
        except Exception as e:
            logger.error(f"Force key update error: {e}")
            return False

def main():
    """Main function"""
    print("=== Smart Lamp Local Key Fix ===\n")
    
    manager = LocalKeyManager()
    
    # Show current config
    config = manager.load_config()
    if 'device' in config:
        device = config['device']
        print(f"Current device: {device.get('name', 'Unknown')}")
        print(f"Device ID: {device.get('id', 'Unknown')}")
        print(f"IP Address: {device.get('address', 'Unknown')}")
        print(f"Current local key: {device.get('local_key', 'Not set')}")
        print()
    
    print("Choose an option:")
    print("1. Generate and set new persistent key")
    print("2. Set custom persistent key")
    print("3. Test current connection")
    print("4. Force key update (re-pair)")
    print("5. View current configuration")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        # Generate new persistent key
        if manager.set_persistent_key():
            print("\n✅ Persistent key set! Testing connection...")
            manager.test_connection()
        else:
            print("\n❌ Failed to set persistent key")
    
    elif choice == '2':
        # Set custom key
        custom_key = input("Enter custom local key (16 chars, hex): ").strip().upper()
        if len(custom_key) == 16 and all(c in '0123456789ABCDEF' for c in custom_key):
            if manager.set_persistent_key(custom_key):
                print("\n✅ Custom persistent key set! Testing connection...")
                manager.test_connection()
            else:
                print("\n❌ Failed to set custom key")
        else:
            print("❌ Invalid key format. Must be 16 hexadecimal characters.")
    
    elif choice == '3':
        # Test connection
        print("\nTesting current connection...")
        if manager.test_connection():
            print("✅ Connection working!")
        else:
            print("❌ Connection failed")
    
    elif choice == '4':
        # Force key update
        print("\nAttempting force key update...")
        if manager.force_key_update():
            print("✅ Key update successful!")
        else:
            print("❌ Key update failed")
    
    elif choice == '5':
        # View config
        print("\nCurrent configuration:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
