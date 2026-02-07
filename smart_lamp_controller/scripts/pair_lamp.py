#!/usr/bin/env python3
"""
Smart Lamp Pairing Script
Connects to a Tuya smart lamp when it's in pairing mode
"""
import json
import time
import logging
import tinytuya
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LampPairer:
    """Handles lamp discovery and pairing"""
    
    def __init__(self):
        self.config_file = "lamp_config.json"
        self.paired_devices = []
        
    def discover_lamps(self) -> list:
        """Discover Tuya devices on the network"""
        logger.info("Scanning for Tuya devices...")
        logger.info("Make sure your lamp is in pairing mode (usually power cycling 5+ times)")
        logger.info("For direct PC pairing: Connect your PC to the lamp's temporary WiFi network")
        
        try:
            # Discover devices (without timeout parameter)
            devices = tinytuya.deviceScan()
            
            if not devices:
                logger.warning("No devices found.")
                logger.info("Try these steps:")
                logger.info("1. Put lamp in pairing mode (power cycle 5+ times until blinking)")
                logger.info("2. Connect your PC directly to the lamp's temporary WiFi")
                logger.info("3. Run this script again")
                logger.info("4. Or manually enter device details if you know the IP")
                return []
            
            logger.info(f"Found {len(devices)} device(s):")
            for i, (ip, device_info) in enumerate(devices.items()):
                logger.info(f"{i+1}. IP: {ip}")
                logger.info(f"   ID: {device_info.get('gwId', 'Unknown')}")
                logger.info(f"   Version: {device_info.get('version', 'Unknown')}")
                logger.info(f"   Product Key: {device_info.get('productKey', 'Unknown')}")
                print()
            
            return list(devices.items())
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return []
    
    def pair_device(self, ip: str, device_id: str, version: str = "3.5") -> Optional[Dict[str, Any]]:
        """Attempt to pair with a specific device"""
        logger.info(f"Attempting to pair with device {device_id} at {ip}")
        
        try:
            # Create device instance without local_key (will be generated)
            device = tinytuya.BulbDevice(
                dev_id=device_id,
                address=ip,
                local_key=""  # Empty key for pairing
            )
            
            device.set_version(float(version))
            
            # Try to connect and get status
            logger.info("Testing connection...")
            data = device.status()
            
            if 'Error' in str(data):
                logger.error(f"Connection failed: {data}")
                return None
            
            logger.info("✅ Successfully connected!")
            
            # Try to get device info
            try:
                info = device.info()
                logger.info(f"Device info: {info}")
            except:
                logger.warning("Could not retrieve detailed device info")
            
            # Test basic control
            logger.info("Testing basic control...")
            try:
                # Turn on
                device.turn_on()
                time.sleep(1)
                
                # Set a test color (red)
                device.set_colour(255, 0, 0)
                time.sleep(2)
                
                # Turn off
                device.turn_off()
                
                logger.info("✅ Basic control test passed!")
                
            except Exception as e:
                logger.warning(f"Control test failed: {e}")
            
            return {
                'id': device_id,
                'address': ip,
                'local_key': device.local_key,  # Generated key
                'version': version,
                'name': f"Smart Lamp {device_id[:8]}"
            }
            
        except Exception as e:
            logger.error(f"Pairing failed: {e}")
            return None
    
    def save_config(self, device_config: Dict[str, Any]):
        """Save device configuration to file"""
        try:
            # Load existing config
            config = {}
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except FileNotFoundError:
                pass
            
            # Update device section
            config['device'] = device_config
            
            # Ensure other sections exist
            if 'ui' not in config:
                config['ui'] = {
                    "window_width": 650,
                    "window_height": 750,
                    "theme": "default"
                }
            
            if 'data_points' not in config:
                config['data_points'] = {
                    "power": "20",
                    "mode": "21", 
                    "brightness": "22",
                    "temperature": "23",
                    "scene": "25"
                }
            
            # Save config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Configuration saved to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def manual_pair_device(self) -> Optional[Dict[str, Any]]:
        """Manually enter device details for pairing"""
        print("\n=== Manual Device Pairing ===")
        print("Enter the device details when prompted:")
        
        try:
            ip = input("Device IP address (e.g., 192.168.4.1): ").strip()
            if not ip:
                logger.error("IP address is required")
                return None
            
            device_id = input("Device ID (leave empty to auto-discover): ").strip()
            if not device_id:
                device_id = f"device_{int(time.time())}"
            
            version = input("Device version (default: 3.5): ").strip()
            if not version:
                version = "3.5"
            
            return self.pair_device(ip, device_id, version)
            
        except KeyboardInterrupt:
            print("\nPairing cancelled.")
    def interactive_pairing(self):
        """Interactive pairing process"""
        print("=== Smart Lamp Pairing Tool ===\n")
        
        # First try automatic discovery
        devices = self.discover_lamps()
        
        if not devices:
            print("\nNo devices found automatically.")
            choice = input("Try manual pairing? (y/n): ").lower()
            if choice != 'y':
                print("\nPairing cancelled.")
                return
            
            # Try manual pairing
            device_config = self.manual_pair_device()
            if device_config:
                self.handle_successful_pairing(device_config)
            return
        
        # Let user select device
        while True:
            try:
                choice = input(f"\nSelect device to pair (1-{len(devices)}) or 'm' for manual: ")
                
                if choice.lower() == 'm':
                    device_config = self.manual_pair_device()
                    if device_config:
                        self.handle_successful_pairing(device_config)
                    return
                
                if choice.lower() == 'q':
                    return
                
                device_index = int(choice) - 1
                if 0 <= device_index < len(devices):
                    break
                else:
                    print("Invalid selection. Please try again.")
                    
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        # Get selected device
        ip, device_info = devices[device_index]
        device_id = device_info.get('gwId', '')
        version = device_info.get('version', '3.5')
        
        # Attempt pairing
        device_config = self.pair_device(ip, device_id, version)
        
        if device_config:
            self.handle_successful_pairing(device_config)
        else:
            print("\n❌ Pairing failed. Please check the lamp and try again.")
    
    def handle_successful_pairing(self, device_config: Dict[str, Any]):
        """Handle successful device pairing"""
        print(f"\n✅ Successfully paired with {device_config['name']}!")
        print(f"Device ID: {device_config['id']}")
        print(f"IP Address: {device_config['address']}")
        print(f"Local Key: {device_config['local_key']}")
        
        # Ask to save config
        save = input("\nSave configuration? (y/n): ").lower()
        if save == 'y':
            self.save_config(device_config)
            print("Configuration saved! You can now use the main application.")

def main():
    """Main function"""
    pairer = LampPairer()
    
    try:
        pairer.interactive_pairing()
    except KeyboardInterrupt:
        print("\n\nPairing cancelled by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
