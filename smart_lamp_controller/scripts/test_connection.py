#!/usr/bin/env python3
"""
Test direct connection to the lamp
"""
import json
import tinytuya

def test_connection():
    """Test connection using current config"""
    try:
        # Load config
        with open('lamp_config.json', 'r') as f:
            config = json.load(f)
        
        device_config = config['device']
        
        print(f"Testing connection to {device_config['name']}")
        print(f"Device ID: {device_config['id']}")
        print(f"IP Address: {device_config['address']}")
        print(f"Local Key: {device_config['local_key']}")
        print(f"Version: {device_config['version']}")
        print()
        
        # Create device
        device = tinytuya.BulbDevice(
            dev_id=device_config['id'],
            address=device_config['address'],
            local_key=device_config['local_key']
        )
        
        device.set_version(float(device_config['version']))
        device.set_socketPersistent(True)
        
        print("Testing connection...")
        data = device.status()
        
        if 'Error' in str(data):
            print(f"❌ Connection failed: {data}")
            return False
        else:
            print("✅ Connection successful!")
            print(f"Device status: {json.dumps(data, indent=2)}")
            
            # Test basic control
            print("\nTesting basic control...")
            
            # Turn on
            print("Turning on...")
            device.turn_on()
            
            # Set red color
            print("Setting red color...")
            device.set_colour(255, 0, 0)
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Turn off
            print("Turning off...")
            device.turn_off()
            
            print("✅ Basic control test passed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
