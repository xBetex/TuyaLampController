#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guide: How to use your Tuya Cloud credentials to get local_key
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def show_web_interface_method():
    """Show how to get key from web interface"""
    print("=" * 70)
    print("🌐 METHOD 1: Get Key from Tuya IoT Platform Web Interface")
    print("=" * 70)
    print("\nYour credentials:")
    print(f"  Access ID: YOUR_TUYA_ACCESS_ID")
    print(f"  Access Secret: YOUR_TUYA_ACCESS_SECRET")
    print(f"  Project Code: YOUR_PROJECT_CODE")
    print(f"  Device ID: YOUR_DEVICE_ID")
    print("\nSteps to get local_key:")
    print("\n1. Go to: https://iot.tuya.com/")
    print("2. Login with your account")
    print("3. Go to your project (Project Code: YOUR_PROJECT_CODE)")
    print("4. Navigate to: Device Management")
    print("5. Find your Avant lamp (Device ID: YOUR_DEVICE_ID)")
    print("6. Click on the device")
    print("7. Look for these fields:")
    print("   - 'Local Key'")
    print("   - 'Device Secret'")
    print("   - 'local_key'")
    print("   - 'localKey'")
    print("8. Copy the value")
    print("\n💡 The key is usually 16 characters long (hex)")
    print("=" * 70)


def show_api_method():
    """Show how to use API (if signature is fixed)"""
    print("\n" + "=" * 70)
    print("🔧 METHOD 2: Use Tuya Cloud API (Advanced)")
    print("=" * 70)
    print("\nThe API signature generation is complex.")
    print("You can use the official Tuya Python SDK instead:\n")
    print("1. Install Tuya IoT SDK:")
    print("   pip install tuya-iot-py-sdk")
    print("\n2. Use this code:")
    print("""
from tuya_iot import TuyaOpenAPI

# Initialize
openapi = TuyaOpenAPI(
    "https://openapi.tuyaus.com",  # or .tuyaeu.com or .tuyacn.com
    "YOUR_TUYA_ACCESS_ID",
    "YOUR_TUYA_ACCESS_SECRET"
)

# Get token
openapi.connect()

# Get device info
response = openapi.get(f"/v1.0/devices/YOUR_DEVICE_ID")
if response.get("success"):
    device_info = response.get("result")
    local_key = device_info.get("local_key")
    print(f"Local Key: {local_key}")
""")
    print("\n⚠️  Note: You need to know your region (US/EU/CN)")
    print("=" * 70)


def show_wizard_method():
    """Show tinytuya wizard method"""
    print("\n" + "=" * 70)
    print("🧙 METHOD 3: Use tinytuya Wizard (Easiest)")
    print("=" * 70)
    print("\nEven though you have cloud credentials, the wizard is still easiest:")
    print("\n1. Run: python -m tinytuya wizard")
    print("2. It will scan your network")
    print("3. Find your Avant lamp")
    print("4. While wizard runs, control lamp from Tuya Smart app")
    print("5. Wizard captures key from network traffic")
    print("6. Key saved to devices.json")
    print("\n✅ This doesn't need cloud API at all!")
    print("=" * 70)


def create_key_file_template():
    """Create a template file for the key"""
    template = """# Avant Lamp Local Key
# Paste your local_key here after getting it from Tuya IoT Platform

AVANT_LOCAL_KEY = "YOUR_LOCAL_KEY_HERE"

# Instructions:
# 1. Go to https://iot.tuya.com/
# 2. Login and go to your project
# 3. Device Management → Find your Avant lamp
# 4. Click on device → Look for "Local Key" or "Device Secret"
# 5. Copy the value and paste it above
# 6. Save this file
"""
    
    with open("avant_key_config.py", "w", encoding="utf-8") as f:
        f.write(template)
    
    print("\n✅ Created: avant_key_config.py")
    print("   Use this file to store your local_key")


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🔑 Using Your Tuya Cloud Credentials")
    print("=" * 70)
    print("\nYou have Tuya Cloud API credentials!")
    print("Here's how to get your Avant lamp's local_key:\n")
    
    show_web_interface_method()
    show_api_method()
    show_wizard_method()
    
    create_key_file_template()
    
    print("\n" + "=" * 70)
    print("📝 RECOMMENDED APPROACH")
    print("=" * 70)
    print("\n✅ EASIEST: Use the web interface (Method 1)")
    print("   1. Login to https://iot.tuya.com/")
    print("   2. Go to Device Management")
    print("   3. Find your device and get the local_key")
    print("   4. Copy it to avant_key_config.py or avant_control.py")
    print("\n✅ ALTERNATIVE: Use tinytuya wizard (Method 3)")
    print("   - No cloud API needed")
    print("   - Works directly from network")
    print("=" * 70)
    print("\n💡 Once you have the key, update avant_control.py:")
    print("   AVANT_KEY = \"your_actual_key_here\"")
    print("   Then run: python avant_control.py off")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
