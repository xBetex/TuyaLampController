#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Local Key from Tuya Cloud API using your credentials
"""

import sys
import requests
import time
import hashlib
import hmac
import base64
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Your Tuya Cloud API Credentials
ACCESS_ID = "YOUR_TUYA_ACCESS_ID"
ACCESS_SECRET = "YOUR_TUYA_ACCESS_SECRET"
PROJECT_CODE = "YOUR_PROJECT_CODE"

# Your Avant Lamp Device ID
DEVICE_ID = "YOUR_DEVICE_ID"

# Tuya API endpoints (try different regions)
REGIONS = {
    "us": "https://openapi.tuyaus.com",
    "eu": "https://openapi.tuyaeu.com",
    "cn": "https://openapi.tuyacn.com",
}


def generate_sign(method, url, headers, body, secret):
    """Generate Tuya API signature"""
    timestamp = headers.get("t", "")
    nonce = headers.get("client_id", "")
    
    # Build string to sign
    string_to_sign = f"{method}\n"
    string_to_sign += f"{hashlib.sha256(body.encode('utf-8')).hexdigest()}\n"
    string_to_sign += f"{headers.get('client_id', '')}\n"
    string_to_sign += f"{timestamp}\n"
    string_to_sign += url.split('?')[0]  # Path without query
    
    # Generate signature
    sign = hmac.new(
        secret.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    
    return sign


def get_access_token(region="us"):
    """Get access token from Tuya Cloud"""
    base_url = REGIONS[region]
    url = f"{base_url}/v1.0/token?grant_type=1"
    
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        "client_id": ACCESS_ID,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
    }
    
    # Build body
    body = ""
    
    # Generate sign
    sign = generate_sign("GET", url, headers, body, ACCESS_SECRET)
    headers["sign"] = sign
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["result"]["access_token"]
            else:
                print(f"❌ Token error: {data.get('msg', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return None


def get_device_info(access_token, device_id, region="us"):
    """Get device information including local_key"""
    base_url = REGIONS[region]
    url = f"{base_url}/v1.0/devices/{device_id}"
    
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        "client_id": ACCESS_ID,
        "access_token": access_token,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
    }
    
    body = ""
    sign = generate_sign("GET", url, headers, body, ACCESS_SECRET)
    headers["sign"] = sign
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["result"]
            else:
                print(f"❌ Device info error: {data.get('msg', 'Unknown error')}")
                if "28841001" in str(data):
                    print("   This is a permissions error. Check:")
                    print("   - Device is linked to your project")
                    print("   - IoT Core service is enabled")
                    print("   - API permissions are correct")
                return None
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting device info: {e}")
        return None


def list_devices(access_token, region="us"):
    """List all devices in the project"""
    base_url = REGIONS[region]
    url = f"{base_url}/v1.0/users/{access_token}/devices"
    
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        "client_id": ACCESS_ID,
        "access_token": access_token,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
    }
    
    body = ""
    sign = generate_sign("GET", url, headers, body, ACCESS_SECRET)
    headers["sign"] = sign
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["result"]
            else:
                print(f"❌ List devices error: {data.get('msg', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error listing devices: {e}")
        return None


def main():
    """Main function"""
    print("=" * 70)
    print("🔑 Getting Local Key from Tuya Cloud API")
    print("=" * 70)
    print(f"\nAccess ID: {ACCESS_ID}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"Project Code: {PROJECT_CODE}\n")
    
    # Try different regions
    regions_to_try = ["us", "eu", "cn"]
    
    for region in regions_to_try:
        print(f"\n{'='*70}")
        print(f"Trying region: {region.upper()}")
        print(f"{'='*70}\n")
        
        # Get access token
        print("Step 1: Getting access token...")
        access_token = get_access_token(region)
        
        if not access_token:
            print(f"❌ Failed to get token for {region}")
            continue
        
        print(f"✅ Got access token: {access_token[:20]}...")
        
        # Try to list devices first
        print("\nStep 2: Listing devices in project...")
        devices = list_devices(access_token, region)
        
        if devices:
            print(f"✅ Found {len(devices)} device(s) in project:")
            for device in devices:
                device_id = device.get("id", "Unknown")
                device_name = device.get("name", "Unknown")
                print(f"   - {device_name} (ID: {device_id})")
                
                if device_id == DEVICE_ID:
                    print(f"\n   ✅ Found your Avant lamp!")
                    local_key = device.get("local_key") or device.get("localKey")
                    if local_key:
                        print(f"\n🎉 LOCAL KEY FOUND: {local_key}")
                        print(f"\nUse this key in avant_control.py:")
                        print(f"   AVANT_KEY = \"{local_key}\"")
                        return local_key
                    else:
                        print("   ⚠️  Local key not in device list, trying device details...")
        
        # Try to get specific device info
        print(f"\nStep 3: Getting device details for {DEVICE_ID}...")
        device_info = get_device_info(access_token, DEVICE_ID, region)
        
        if device_info:
            print(f"✅ Got device info:")
            print(f"   Name: {device_info.get('name', 'Unknown')}")
            print(f"   ID: {device_info.get('id', 'Unknown')}")
            print(f"   Online: {device_info.get('online', False)}")
            
            # Look for local_key in various possible fields
            local_key = (
                device_info.get("local_key") or
                device_info.get("localKey") or
                device_info.get("device_secret") or
                device_info.get("secret") or
                device_info.get("key")
            )
            
            if local_key:
                print(f"\n🎉 LOCAL KEY FOUND: {local_key}")
                print(f"\nUse this key in avant_control.py:")
                print(f"   AVANT_KEY = \"{local_key}\"")
                
                # Save to file
                with open("avant_key.txt", "w") as f:
                    f.write(local_key)
                print(f"\n✅ Key saved to: avant_key.txt")
                
                return local_key
            else:
                print("\n❌ Local key not found in device info")
                print("   Available fields:", list(device_info.keys())[:10])
                print("\n   This might mean:")
                print("   - Device doesn't support local control")
                print("   - Local key is not exposed via API")
                print("   - Try using tinytuya wizard instead")
        else:
            print(f"❌ Failed to get device info for {region}")
    
    print("\n" + "=" * 70)
    print("❌ Could not get local_key from Cloud API")
    print("=" * 70)
    print("\nTry these alternatives:")
    print("1. Use tinytuya wizard: python -m tinytuya wizard")
    print("2. Check Tuya IoT Platform web interface directly")
    print("3. Make sure device is properly linked to your project")
    print("=" * 70)
    
    return None


if __name__ == "__main__":
    main()
