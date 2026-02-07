#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Local Key using TinyTuya Cloud Class
Uses the built-in Cloud class which may have better access
"""

import sys
import os
import tinytuya
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Your Tuya Cloud Credentials
ACCESS_ID = "YOUR_TUYA_ACCESS_ID"
ACCESS_SECRET = "YOUR_TUYA_ACCESS_SECRET"
DEVICE_ID = "YOUR_DEVICE_ID"

# Try different regions
REGIONS = ["us", "eu", "cn"]


def try_cloud_methods(region):
    """Try different Cloud methods to get local_key"""
    print(f"\n{'='*70}")
    print(f"Trying Region: {region.upper()}")
    print(f"{'='*70}\n")
    
    try:
        # Initialize Cloud connection
        print(f"Step 1: Initializing Cloud connection...")
        cloud = tinytuya.Cloud(
            apiRegion=region,
            apiKey=ACCESS_ID,
            apiSecret=ACCESS_SECRET,
            apiDeviceID=DEVICE_ID,
            new_sign_algorithm=True
        )
        print("✅ Cloud object created")
        
        # Method 1: Get devices list
        print(f"\nStep 2: Getting devices list...")
        try:
            devices = cloud.getdevices(verbose=True)
            if devices:
                print(f"✅ Found {len(devices)} device(s)")
                for device in devices:
                    dev_id = device.get("id", "Unknown")
                    dev_name = device.get("name", "Unknown")
                    print(f"   - {dev_name} (ID: {dev_id})")
                    
                    # Check if this is our device
                    if dev_id == DEVICE_ID:
                        print(f"\n   ✅ Found your Avant lamp!")
                        # Look for local_key in device data
                        local_key = (
                            device.get("local_key") or
                            device.get("localKey") or
                            device.get("device_secret") or
                            device.get("secret") or
                            device.get("key")
                        )
                        if local_key:
                            print(f"\n🎉 LOCAL KEY FOUND: {local_key}")
                            return local_key
                        else:
                            print("   ⚠️  Local key not in device list data")
                            print(f"   Available keys: {list(device.keys())[:10]}")
            else:
                print("❌ No devices returned")
        except Exception as e:
            print(f"❌ getdevices() failed: {e}")
        
        # Method 2: Get device properties
        print(f"\nStep 3: Getting device properties...")
        try:
            properties = cloud.getproperties(DEVICE_ID)
            if properties:
                print(f"✅ Got properties: {json.dumps(properties, indent=2)[:200]}...")
                # Look for local_key in properties
                if isinstance(properties, dict):
                    local_key = (
                        properties.get("local_key") or
                        properties.get("localKey") or
                        properties.get("device_secret")
                    )
                    if local_key:
                        print(f"\n🎉 LOCAL KEY FOUND in properties: {local_key}")
                        return local_key
        except Exception as e:
            print(f"❌ getproperties() failed: {e}")
        
        # Method 3: Get device functions
        print(f"\nStep 4: Getting device functions...")
        try:
            functions = cloud.getfunctions(DEVICE_ID)
            if functions:
                print(f"✅ Got functions: {json.dumps(functions, indent=2)[:200]}...")
        except Exception as e:
            print(f"❌ getfunctions() failed: {e}")
        
        # Method 4: Get device status (might contain key info)
        print(f"\nStep 5: Getting device status...")
        try:
            status = cloud.getstatus(DEVICE_ID)
            if status:
                print(f"✅ Got status: {json.dumps(status, indent=2)[:200]}...")
        except Exception as e:
            print(f"❌ getstatus() failed: {e}")
        
        # Method 5: Get device DPS
        print(f"\nStep 6: Getting device DPS...")
        try:
            dps = cloud.getdps(DEVICE_ID)
            if dps:
                print(f"✅ Got DPS: {json.dumps(dps, indent=2)[:200]}...")
        except Exception as e:
            print(f"❌ getdps() failed: {e}")
        
        # Method 6: Try cloudrequest directly
        print(f"\nStep 7: Trying direct API request for device details...")
        try:
            # Try to get device details directly
            url = f"/v1.0/devices/{DEVICE_ID}"
            response = cloud.cloudrequest(url, action="GET")
            if response:
                print(f"✅ Direct request response:")
                print(json.dumps(response, indent=2)[:500])
                
                # Look for local_key in response
                if isinstance(response, dict):
                    result = response.get("result", {})
                    local_key = (
                        result.get("local_key") or
                        result.get("localKey") or
                        result.get("device_secret") or
                        result.get("secret")
                    )
                    if local_key:
                        print(f"\n🎉 LOCAL KEY FOUND in direct request: {local_key}")
                        return local_key
        except Exception as e:
            print(f"❌ Direct request failed: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ Cloud initialization failed: {e}")
        return None


def main():
    """Main function"""
    print("=" * 70)
    print("🔑 Getting Local Key using TinyTuya Cloud Class")
    print("=" * 70)
    print(f"\nAccess ID: {ACCESS_ID}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"\nTrying different regions and methods...\n")
    
    found_key = None
    
    # Try each region
    for region in REGIONS:
        key = try_cloud_methods(region)
        if key:
            found_key = key
            break
    
    # Summary
    print("\n" + "=" * 70)
    if found_key:
        print("🎉 SUCCESS! Local Key Found!")
        print("=" * 70)
        print(f"\nYour local_key: {found_key}")
        print(f"\nUpdate avant_control.py:")
        print(f'   AVANT_KEY = "{found_key}"')
        
        # Save to file
        with open("avant_key.txt", "w") as f:
            f.write(found_key)
        print(f"\n✅ Key saved to: avant_key.txt")
        
        # Also update avant_control.py if it exists
        try:
            with open("avant_control.py", "r", encoding="utf-8") as f:
                content = f.read()
            
            if "YOUR_LOCAL_KEY_HERE" in content:
                new_content = content.replace(
                    'AVANT_KEY = "YOUR_LOCAL_KEY_HERE"',
                    f'AVANT_KEY = "{found_key}"'
                )
                with open("avant_control.py", "w", encoding="utf-8") as f:
                    f.write(new_content)
                print("✅ Updated avant_control.py with your key!")
        except:
            pass
        
    else:
        print("❌ Could Not Get Local Key from Cloud API")
        print("=" * 70)
        print("\nThe Cloud API methods didn't return the local_key.")
        print("\nTry these alternatives:")
        print("1. Web Interface: https://iot.tuya.com/ → Device Management")
        print("2. Network packet capture (Wireshark)")
        print("3. Extract from Tuya Smart app (if rooted)")
        print("\nThe local_key might not be exposed via API due to:")
        print("  - API permissions restrictions")
        print("  - Device security settings")
        print("  - Tuya policy changes")
    
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
