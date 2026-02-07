#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse device list from TinyTuya Cloud to find local_key
"""

import sys
import tinytuya
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

ACCESS_ID = "YOUR_TUYA_ACCESS_ID"
ACCESS_SECRET = "YOUR_TUYA_ACCESS_SECRET"
DEVICE_ID = "YOUR_DEVICE_ID"

def main():
    print("=" * 70)
    print("Parsing Device List from Cloud")
    print("=" * 70)
    
    # Try US region
    try:
        cloud = tinytuya.Cloud(
            apiRegion="us",
            apiKey=ACCESS_ID,
            apiSecret=ACCESS_SECRET,
            apiDeviceID=DEVICE_ID,
            new_sign_algorithm=True
        )
        
        print("\nGetting devices list...")
        devices = cloud.getdevices(verbose=True)
        
        print(f"\nRaw response type: {type(devices)}")
        print(f"Raw response: {devices}")
        
        # Try to parse it properly
        if isinstance(devices, list):
            print(f"\n✅ Got {len(devices)} devices as list")
            for i, device in enumerate(devices):
                print(f"\nDevice {i+1}:")
                if isinstance(device, dict):
                    print(json.dumps(device, indent=2))
                    # Look for our device
                    if device.get("id") == DEVICE_ID:
                        local_key = device.get("local_key") or device.get("localKey")
                        if local_key:
                            print(f"\n🎉 FOUND LOCAL KEY: {local_key}")
                            return local_key
                else:
                    print(f"  Type: {type(device)}, Value: {device}")
        elif isinstance(devices, dict):
            print(f"\n✅ Got devices as dict")
            print(json.dumps(devices, indent=2))
            # Check if result is nested
            if "result" in devices:
                result = devices["result"]
                if isinstance(result, list):
                    for device in result:
                        if isinstance(device, dict) and device.get("id") == DEVICE_ID:
                            local_key = device.get("local_key") or device.get("localKey")
                            if local_key:
                                print(f"\n🎉 FOUND LOCAL KEY: {local_key}")
                                return local_key
        elif isinstance(devices, str):
            print(f"\n⚠️  Got string response, trying to parse as JSON...")
            try:
                parsed = json.loads(devices)
                print(json.dumps(parsed, indent=2))
            except:
                print(f"Could not parse as JSON")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("Could not extract local_key from device list")
    print("=" * 70)
    print("\nThe API is still blocking access due to permissions.")
    print("Best solution: Use the web interface at https://iot.tuya.com/")
    print("=" * 70)

if __name__ == "__main__":
    main()
