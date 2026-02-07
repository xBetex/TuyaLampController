#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete Key Analysis - Show everything knowable about the key and device
"""

import sys
import os
import json
import tinytuya
import time
import hashlib

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_key_from_files():
    """Try to load key from various files"""
    print("=" * 70)
    print("📁 Loading Key from Files")
    print("=" * 70)
    
    key_sources = {}
    
    # Check tinytuya.json
    files_to_check = [
        "tinytuya.json",
        "devices.json",
        "avant_key.txt",
        "avant_key_config.py",
        "avant_control.py"
    ]
    
    for filename in files_to_check:
        if os.path.exists(filename):
            print(f"\n✅ Found: {filename}")
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                if filename.endswith(".json"):
                    data = json.loads(content)
                    print(f"   Content: {json.dumps(data, indent=2)}")
                    
                    # Look for key in various formats
                    if isinstance(data, dict):
                        # Check for device with our ID
                        if "devices" in data:
                            for device in data.get("devices", []):
                                if device.get("id") == "YOUR_DEVICE_ID":
                                    key = device.get("key") or device.get("local_key") or device.get("localKey")
                                    if key:
                                        key_sources[filename] = key
                                        print(f"   🎉 Found key: {key}")
                        # Check top level
                        key = data.get("key") or data.get("local_key") or data.get("localKey")
                        if key:
                            key_sources[filename] = key
                            print(f"   🎉 Found key: {key}")
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("id") == "YOUR_DEVICE_ID":
                                key = item.get("key") or item.get("local_key")
                                if key:
                                    key_sources[filename] = key
                                    print(f"   🎉 Found key: {key}")
                elif filename.endswith(".txt"):
                    key = content.strip()
                    if key and len(key) >= 8:
                        key_sources[filename] = key
                        print(f"   🎉 Found key: {key}")
                elif filename.endswith(".py"):
                    # Extract key from Python file
                    import re
                    matches = re.findall(r'AVANT_KEY\s*=\s*["\']([^"\']+)["\']', content)
                    if matches:
                        key = matches[0]
                        if key != "YOUR_LOCAL_KEY_HERE":
                            key_sources[filename] = key
                            print(f"   🎉 Found key: {key}")
            except Exception as e:
                print(f"   ⚠️  Error reading: {e}")
        else:
            print(f"\n❌ Not found: {filename}")
    
    return key_sources


def analyze_key(key):
    """Analyze the key itself"""
    print("\n" + "=" * 70)
    print("🔍 Key Analysis")
    print("=" * 70)
    
    print(f"\nKey Value: {key}")
    print(f"Length: {len(key)} characters")
    print(f"Type: {type(key).__name__}")
    
    # Character analysis
    print(f"\nCharacter Analysis:")
    print(f"  - Contains letters: {any(c.isalpha() for c in key)}")
    print(f"  - Contains digits: {any(c.isdigit() for c in key)}")
    print(f"  - Contains hex chars only: {all(c in '0123456789abcdefABCDEF' for c in key)}")
    print(f"  - All lowercase: {key.islower()}")
    print(f"  - All uppercase: {key.isupper()}")
    print(f"  - Mixed case: {not (key.islower() or key.isupper())}")
    
    # Common key patterns
    print(f"\nPattern Analysis:")
    if len(key) == 16:
        print(f"  ✅ Standard length (16 characters - typical for Tuya)")
    elif len(key) == 32:
        print(f"  ⚠️  Long key (32 characters - might be double-encoded)")
    else:
        print(f"  ⚠️  Non-standard length ({len(key)} characters)")
    
    # Try to detect if it's hex
    try:
        bytes.fromhex(key)
        print(f"  ✅ Valid hexadecimal")
    except:
        print(f"  ⚠️  Not valid hexadecimal")
    
    # Hash analysis
    print(f"\nHash Analysis:")
    md5 = hashlib.md5(key.encode()).hexdigest()
    sha256 = hashlib.sha256(key.encode()).hexdigest()
    print(f"  MD5: {md5}")
    print(f"  SHA256: {sha256[:32]}...")
    
    return key


def test_key_with_device(key):
    """Test the key with the actual device"""
    print("\n" + "=" * 70)
    print("🧪 Testing Key with Device")
    print("=" * 70)
    
    device_ip = "YOUR_DEVICE_IP"
    device_id = "YOUR_DEVICE_ID"
    version = "3.5"
    
    print(f"\nDevice: {device_id} @ {device_ip}")
    print(f"Version: {version}")
    print(f"Key: {key[:8]}... (showing first 8 chars)")
    
    # Test with different versions
    versions = ["3.1", "3.3", "3.4", "3.5"]
    
    for v in versions:
        print(f"\nTesting with version {v}...")
        try:
            d = tinytuya.Device(device_id, device_ip)
            d.set_version(v)
            d.set_key(key)
            
            # Try to get status
            status = d.status()
            
            if status.get("Error"):
                error = status.get("Error", "")
                if "key" in error.lower() or "914" in error:
                    print(f"  ❌ Key authentication failed: {error}")
                else:
                    print(f"  ⚠️  Different error (might be progress): {error}")
            else:
                print(f"  ✅ KEY WORKS! Status: {status}")
                
                # Try control
                print(f"  Testing control...")
                result = d.turn_off()
                if result.get("Error"):
                    print(f"  ⚠️  Status OK but control failed: {result.get('Error')}")
                else:
                    print(f"  ✅ CONTROL WORKS! Key is fully functional!")
                    return True, v
        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:50]}")
    
    return False, None


def get_device_info_from_network():
    """Get device info from network scan"""
    print("\n" + "=" * 70)
    print("🌐 Network Device Information")
    print("=" * 70)
    
    try:
        devices = tinytuya.deviceScan()
        if devices:
            for ip, info in devices.items():
                if ip == "YOUR_DEVICE_IP":
                    print(f"\n✅ Found your device:")
                    print(f"  IP: {ip}")
                    print(f"  Device ID: {info.get('gwId', 'Unknown')}")
                    print(f"  Version: {info.get('version', 'Unknown')}")
                    print(f"  Full info: {json.dumps(info, indent=2)}")
                    return info
    except Exception as e:
        print(f"❌ Scan failed: {e}")
    
    return None


def show_key_usage_examples(key):
    """Show how to use the key"""
    print("\n" + "=" * 70)
    print("📝 Key Usage Examples")
    print("=" * 70)
    
    print(f"\n1. Basic Control:")
    print(f"""
import tinytuya

d = tinytuya.Device("YOUR_DEVICE_ID", "YOUR_DEVICE_IP")
d.set_version("3.5")
d.set_key("{key}")
d.turn_off()
d.turn_on()
""")
    
    print(f"\n2. In avant_control.py:")
    print(f"""
AVANT_KEY = "{key}"
""")
    
    print(f"\n3. Save to file:")
    print(f"""
with open("key.txt", "w") as f:
    f.write("{key}")
""")


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("🔑 COMPLETE KEY ANALYSIS")
    print("=" * 70)
    print("\nAnalyzing everything knowable about your Avant lamp key...\n")
    
    # Step 1: Load key from files
    key_sources = load_key_from_files()
    
    if not key_sources:
        print("\n❌ No key found in any files!")
        print("\nYou need to:")
        print("1. Get key from Tuya IoT Platform web interface")
        print("2. Or extract from network packets")
        print("3. Or get from Tuya Smart app")
        return
    
    # Use first key found
    source_file = list(key_sources.keys())[0]
    key = key_sources[source_file]
    
    print(f"\n✅ Using key from: {source_file}")
    
    # Step 2: Analyze the key
    analyzed_key = analyze_key(key)
    
    # Step 3: Test with device
    works, working_version = test_key_with_device(key)
    
    # Step 4: Get network info
    device_info = get_device_info_from_network()
    
    # Step 5: Show usage
    if works:
        show_key_usage_examples(key)
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print(f"\nKey Source: {source_file}")
    print(f"Key Length: {len(key)} characters")
    print(f"Key Valid: {'✅ YES' if works else '❌ NO'}")
    if works:
        print(f"Working Version: {working_version}")
        print(f"\n🎉 Your key is VALID and WORKING!")
        print(f"   You can now control your Avant lamp!")
    else:
        print(f"\n⚠️  Key may be invalid or device needs different key")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
