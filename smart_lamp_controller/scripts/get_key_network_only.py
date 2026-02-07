#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Local Key using Network Scanning Only (No Cloud API)
Bypasses the permissions error by using network packet capture
"""

import sys
import os
import tinytuya
import json
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def scan_network_for_devices():
    """Scan network for Tuya devices"""
    print("=" * 70)
    print("🔍 Scanning Network for Tuya Devices")
    print("=" * 70)
    print("\nThis will scan your local network...")
    print("Make sure your Avant lamp is powered on and connected to WiFi.\n")
    
    try:
        print("Scanning... (this may take 30-60 seconds)")
        devices = tinytuya.deviceScan()
        
        if devices:
            print(f"\n✅ Found {len(devices)} device(s):\n")
            for ip, info in devices.items():
                device_id = info.get("gwId", "Unknown")
                version = info.get("version", "Unknown")
                print(f"  IP: {ip}")
                print(f"  Device ID: {device_id}")
                print(f"  Version: {version}")
                print()
            
            return devices
        else:
            print("\n❌ No devices found")
            print("\nMake sure:")
            print("  - Lamp is powered on")
            print("  - Lamp is connected to WiFi")
            print("  - Your computer is on the same network")
            return None
            
    except Exception as e:
        print(f"\n❌ Scan failed: {e}")
        return None


def try_to_get_key_from_packets(device_ip, device_id):
    """Try to capture key from network packets"""
    print("=" * 70)
    print("📡 Network Packet Capture Method")
    print("=" * 70)
    print("\nTo capture the key from network traffic:")
    print("\n1. Install Wireshark: https://www.wireshark.org/")
    print("2. Start Wireshark and capture on your network interface")
    print(f"3. Filter for: ip.addr == {device_ip}")
    print("4. Control your Avant lamp from Tuya Smart app")
    print("5. Look for Tuya protocol packets (port 6668)")
    print("6. Analyze the packets to find the encryption key")
    print("\n⚠️  This requires network analysis knowledge")
    print("=" * 70)


def method_manual_testing():
    """Try to test connection with different approaches"""
    print("=" * 70)
    print("🧪 Manual Testing Method")
    print("=" * 70)
    
    device_ip = "YOUR_DEVICE_IP"
    device_id = "YOUR_DEVICE_ID"
    
    print(f"\nTesting connection to {device_id} @ {device_ip}...\n")
    
    # Try different versions
    versions = ["3.1", "3.3", "3.4", "3.5"]
    
    for version in versions:
        print(f"Trying version {version}...", end=" ")
        try:
            d = tinytuya.Device(device_id, device_ip)
            d.set_version(version)
            
            # Try status without key
            status = d.status()
            
            if status.get("Error"):
                error = status.get("Error", "")
                if "key" in str(error).lower() or "914" in str(error):
                    print("❌ Needs key")
                else:
                    print(f"⚠️  Different error: {error[:30]}")
            else:
                print("✅ Connected! (but may still need key for control)")
        except Exception as e:
            print(f"❌ Failed: {str(e)[:30]}")
    
    print("\n" + "=" * 70)


def method_tuya_smart_app_extract():
    """Instructions for extracting from Tuya Smart app"""
    print("\n" + "=" * 70)
    print("📱 Extract from Tuya Smart App")
    print("=" * 70)
    print("\nIf you have Android with root access:")
    print("\n1. Install Tuya Smart app and add your Avant lamp")
    print("2. Use a file explorer with root access (e.g., Root Explorer)")
    print("3. Navigate to: /data/data/com.tuya.smart/")
    print("4. Find database files (usually .db files)")
    print("5. Open with SQLite viewer (e.g., SQLite Browser)")
    print("6. Look for tables like 'device', 'device_info', or 'tuya_device'")
    print("7. Find your device (ID: YOUR_DEVICE_ID)")
    print("8. Look for column: 'localKey' or 'local_key'")
    print("9. Copy the value")
    print("\n⚠️  Requires root access on Android")
    print("=" * 70)


def create_alternative_script():
    """Create script that tries to work without key"""
    script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alternative: Try to control without key (may work for some devices)
"""

import tinytuya
import sys

DEVICE_ID = "YOUR_DEVICE_ID"
DEVICE_IP = "YOUR_DEVICE_IP"
VERSION = "3.5"

def try_control():
    """Try to control without key"""
    try:
        d = tinytuya.Device(DEVICE_ID, DEVICE_IP)
        d.set_version(VERSION)
        
        # Try without setting key
        print("Trying without key...")
        result = d.turn_off()
        
        if result.get("Error"):
            print(f"❌ Failed: {result.get('Error')}")
            print("\\nYou need the local_key. Try:")
            print("1. Web interface: https://iot.tuya.com/")
            print("2. Network packet capture")
            print("3. Extract from Tuya Smart app")
        else:
            print("✅ Success! Device doesn't require key (unlikely)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try_control()
'''
    
    with open("try_control_no_key.py", "w", encoding="utf-8") as f:
        f.write(script)
    
    print("\n✅ Created: try_control_no_key.py")
    print("   (This will likely fail, but worth trying)")


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🔑 Getting Local Key - Network Methods (No Cloud API)")
    print("=" * 70)
    print("\nSince Cloud API has permissions issues, let's try network methods.\n")
    
    # Scan network
    devices = scan_network_for_devices()
    
    if devices:
        # Check if our device is found
        device_ip = "YOUR_DEVICE_IP"
        device_id = "YOUR_DEVICE_ID"
        
        if device_ip in devices:
            print(f"✅ Found your Avant lamp at {device_ip}")
        else:
            print(f"⚠️  Your lamp ({device_ip}) not in scan results")
            print("   But we know it exists from previous tests")
    
    # Show alternative methods
    print("\n" + "=" * 70)
    print("Alternative Methods (No Cloud API Required)")
    print("=" * 70)
    
    method_manual_testing()
    method_tuya_smart_app_extract()
    try_to_get_key_from_packets("YOUR_DEVICE_IP", "YOUR_DEVICE_ID")
    
    create_alternative_script()
    
    print("\n" + "=" * 70)
    print("💡 RECOMMENDED: Use Web Interface")
    print("=" * 70)
    print("\nSince Cloud API has permissions issues:")
    print("\n1. Go to: https://iot.tuya.com/")
    print("2. Login to your account")
    print("3. Go to Device Management")
    print("4. Find device: YOUR_DEVICE_ID")
    print("5. Click on it and look for 'Local Key'")
    print("6. Copy the value")
    print("7. Use it in avant_control.py")
    print("\n✅ This bypasses all API permission issues!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
