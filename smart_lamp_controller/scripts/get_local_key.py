#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper script to get the local_key for your Tuya device
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def method1_tinytuya_wizard():
    """Method 1: Use tinytuya wizard"""
    print("=" * 70)
    print("METHOD 1: Using tinytuya Wizard (Easiest)")
    print("=" * 70)
    print("\nRun this command in your terminal:")
    print("  python -m tinytuya wizard")
    print("\nThe wizard will:")
    print("  1. Scan your network for Tuya devices")
    print("  2. Help you get the local_key")
    print("  3. Save credentials to a JSON file")
    print("\nAfter running the wizard, you'll have a file like:")
    print("  devices.json or tinytuya.json")
    print("\nOpen that file and find your device's 'key' or 'local_key'")
    print("=" * 70)


def method2_tuya_iot_platform():
    """Method 2: Use Tuya IoT Platform"""
    print("\n" + "=" * 70)
    print("METHOD 2: Tuya IoT Platform (Official Method)")
    print("=" * 70)
    print("\n1. Go to: https://iot.tuya.com/")
    print("2. Create an account (free)")
    print("3. Create a Cloud Project")
    print("4. Link your device to the project")
    print("5. Go to Device Management")
    print("6. Find your device and click on it")
    print("7. Look for 'Local Key' or 'Device Secret'")
    print("\nNote: This method requires linking your device to Tuya Cloud")
    print("=" * 70)


def method3_tuya_smart_app():
    """Method 3: Extract from Tuya Smart app (advanced)"""
    print("\n" + "=" * 70)
    print("METHOD 3: Extract from Tuya Smart App (Advanced)")
    print("=" * 70)
    print("\n⚠️  This method is more complex and may require:")
    print("   - Root access (Android) or Jailbreak (iOS)")
    print("   - Database access to the app's data")
    print("\nSteps (Android with root):")
    print("1. Install Tuya Smart app and add your device")
    print("2. Use a file explorer with root access")
    print("3. Navigate to: /data/data/com.tuya.smart/")
    print("4. Find database files (usually SQLite)")
    print("5. Look for device table with 'localKey' column")
    print("\n⚠️  Not recommended for beginners")
    print("=" * 70)


def method4_scan_and_bruteforce():
    """Method 4: Network scan (limited success)"""
    print("\n" + "=" * 70)
    print("METHOD 4: Network Scan (Limited)")
    print("=" * 70)
    print("\nSome older Tuya devices use default keys.")
    print("You can try scanning with common keys:")
    print("\nCommon default keys to try:")
    print("  - '0123456789abcdef'")
    print("  - 'abcdef0123456789'")
    print("  - Device ID (sometimes)")
    print("\n⚠️  Modern devices don't use default keys")
    print("=" * 70)


def create_working_example():
    """Create a working example script"""
    example_code = '''#!/usr/bin/env python3
"""
Working Lamp Control Example
Replace 'YOUR_LOCAL_KEY_HERE' with your actual local_key
"""

import tinytuya
import time

# Your device information
lamp_ip = "YOUR_DEVICE_IP"
lamp_id = "YOUR_DEVICE_ID"
version = "3.5"
local_key = "YOUR_LOCAL_KEY_HERE"  # <-- REPLACE THIS!

def control_lamp():
    try:
        # Create device connection
        d = tinytuya.Device(lamp_id, lamp_ip)
        d.set_version(version)
        d.set_key(local_key)  # Set the authentication key
        
        # Test connection
        print("Testing connection...")
        status = d.status()
        if status.get("Error"):
            print(f"❌ Error: {status.get('Error')}")
            return False
        
        print("✅ Connected successfully!")
        print(f"Status: {status}")
        
        # Turn lamp OFF
        print("\\nTurning lamp OFF...")
        result = d.turn_off()
        if result.get("Error"):
            print(f"❌ Failed: {result.get('Error')}")
        else:
            print("✅ Lamp turned OFF!")
        
        time.sleep(2)
        
        # Turn lamp ON
        print("\\nTurning lamp ON...")
        result = d.turn_on()
        if result.get("Error"):
            print(f"❌ Failed: {result.get('Error')}")
        else:
            print("✅ Lamp turned ON!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    control_lamp()
'''
    
    with open("working_lamp_control.py", "w", encoding="utf-8") as f:
        f.write(example_code)
    
    print("\n" + "=" * 70)
    print("✅ Created: working_lamp_control.py")
    print("=" * 70)
    print("\nThis file contains a working example.")
    print("Just replace 'YOUR_LOCAL_KEY_HERE' with your actual key.")
    print("=" * 70)


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🔑 HOW TO GET YOUR LAMP'S LOCAL_KEY")
    print("=" * 70)
    print("\nYour lamp requires a 'local_key' (authentication secret)")
    print("to control it. Here are the methods to get it:\n")
    
    method1_tinytuya_wizard()
    method2_tuya_iot_platform()
    method3_tuya_smart_app()
    method4_scan_and_bruteforce()
    
    print("\n" + "=" * 70)
    print("💡 RECOMMENDED: Use Method 1 (tinytuya wizard)")
    print("=" * 70)
    print("\nIt's the easiest and most reliable method.")
    print("\nRun: python -m tinytuya wizard")
    print("=" * 70)
    
    # Create working example
    create_working_example()
    
    print("\n" + "=" * 70)
    print("📝 NEXT STEPS")
    print("=" * 70)
    print("\n1. Get your local_key using one of the methods above")
    print("2. Open 'working_lamp_control.py'")
    print("3. Replace 'YOUR_LOCAL_KEY_HERE' with your actual key")
    print("4. Run: python working_lamp_control.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
