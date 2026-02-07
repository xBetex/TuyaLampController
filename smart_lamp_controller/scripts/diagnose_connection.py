#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic tool to identify why lamp control is failing
Checks authentication, connection, and provides solutions
"""

import sys
import os
import tinytuya
import time
import json

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def diagnose_lamp_connection(lamp_ip, lamp_id, version="3.5"):
    """Diagnose connection issues with the lamp"""
    
    print("=" * 70)
    print("🔍 LAMP CONNECTION DIAGNOSTIC")
    print("=" * 70)
    print(f"Device IP: {lamp_ip}")
    print(f"Device ID: {lamp_id}")
    print(f"Protocol Version: {version}")
    print("=" * 70 + "\n")
    
    # Test 1: Basic connection
    print("TEST 1: Basic Connection Test")
    print("-" * 70)
    try:
        d = tinytuya.Device(lamp_id, lamp_ip)
        d.set_version(version)
        print("✅ Device object created successfully")
    except Exception as e:
        print(f"❌ Failed to create device: {e}")
        return
    
    # Test 2: Status query
    print("\nTEST 2: Status Query")
    print("-" * 70)
    try:
        status = d.status()
        print(f"Response received: {json.dumps(status, indent=2)}")
        
        if "Error" in status or "Err" in status:
            error_msg = status.get("Error") or status.get("Err") or "Unknown error"
            print(f"\n❌ ERROR DETECTED: {error_msg}")
            
            # Common error analysis
            error_str = str(error_msg).lower()
            
            if "key" in error_str or "secret" in error_str or "auth" in error_str:
                print("\n🔑 AUTHENTICATION ERROR DETECTED")
                print("   The device requires a local_key (secret) for authentication.")
                print("\n   Solutions:")
                print("   1. Get the local_key from Tuya IoT Platform:")
                print("      - Go to https://iot.tuya.com/")
                print("      - Create a project and link your device")
                print("      - Get the local_key from device details")
                print("\n   2. Use tinytuya wizard to get the key:")
                print("      - Run: python -m tinytuya wizard")
                print("      - Follow the prompts to scan and get keys")
                print("\n   3. Extract from Tuya Smart app (requires root/jailbreak)")
                print("\n   4. Try using set_key() method:")
                print("      d.set_key('your_local_key_here')")
                
            elif "timeout" in error_str:
                print("\n⏱️  TIMEOUT ERROR")
                print("   The device is not responding in time.")
                print("\n   Solutions:")
                print("   1. Check if device is powered on")
                print("   2. Check network connectivity")
                print("   3. Try increasing timeout")
                
            elif "connection" in error_str or "refused" in error_str:
                print("\n🔌 CONNECTION ERROR")
                print("   Cannot establish connection to device.")
                print("\n   Solutions:")
                print("   1. Verify device IP address")
                print("   2. Check if device is on the same network")
                print("   3. Check firewall settings")
                print("   4. Try different protocol version")
                
            else:
                print(f"\n⚠️  UNKNOWN ERROR: {error_msg}")
                print("   Try the solutions below.")
                
        else:
            print("✅ Status query successful!")
            print("   Device is responding correctly.")
            
    except Exception as e:
        print(f"❌ Status query failed: {e}")
        print(f"   Exception type: {type(e).__name__}")
    
    # Test 3: Try control without key
    print("\n\nTEST 3: Control Command Test (without local_key)")
    print("-" * 70)
    try:
        print("Attempting to turn lamp OFF...")
        result = d.turn_off()
        print(f"Result: {json.dumps(result, indent=2)}")
        
        if result.get("Error"):
            print(f"\n❌ Control failed: {result.get('Error')}")
        else:
            print("✅ Control command sent successfully!")
            time.sleep(2)
            
            print("\nAttempting to turn lamp ON...")
            result = d.turn_on()
            print(f"Result: {json.dumps(result, indent=2)}")
            
    except Exception as e:
        print(f"❌ Control test failed: {e}")
    
    # Test 4: Try with different methods
    print("\n\nTEST 4: Alternative Control Methods")
    print("-" * 70)
    
    methods = [
        ("set_value(1, False)", lambda: d.set_value(1, False)),
        ("set_status(False, 1)", lambda: d.set_status(False, 1)),
        ("set_dps(1, False)", lambda: d.set_dps(1, False) if hasattr(d, 'set_dps') else None),
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"\nTrying {method_name}...")
            if method_func:
                result = method_func()
                if result and not result.get("Error"):
                    print(f"✅ {method_name} succeeded!")
                    break
                elif result:
                    print(f"❌ {method_name} failed: {result.get('Error', 'Unknown error')}")
        except Exception as e:
            print(f"❌ {method_name} exception: {e}")
    
    # Test 5: Protocol version test
    print("\n\nTEST 5: Protocol Version Test")
    print("-" * 70)
    versions = ["3.1", "3.3", "3.4", "3.5", "auto"]
    
    for v in versions:
        try:
            print(f"\nTrying version {v}...")
            d_test = tinytuya.Device(lamp_id, lamp_ip)
            d_test.set_version(v)
            status = d_test.status()
            
            if not status.get("Error") and not status.get("Err"):
                print(f"✅ Version {v} works! Status: {status}")
                break
            else:
                print(f"❌ Version {v} failed: {status.get('Error', status.get('Err'))}")
        except Exception as e:
            print(f"❌ Version {v} exception: {e}")
    
    # Summary and recommendations
    print("\n\n" + "=" * 70)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    print("\nMost likely issue: Missing local_key (authentication secret)")
    print("\nRecommended steps:")
    print("1. Get your device's local_key using one of these methods:")
    print("   a) Tuya IoT Platform (https://iot.tuya.com/)")
    print("   b) tinytuya wizard: python -m tinytuya wizard")
    print("   c) Extract from Tuya Smart app (advanced)")
    print("\n2. Once you have the local_key, use it like this:")
    print("   d = tinytuya.Device(lamp_id, lamp_ip)")
    print("   d.set_version('3.5')")
    print("   d.set_key('your_local_key_here')  # <-- Add this line")
    print("   d.turn_off()")
    print("\n3. Alternative: Use Tuya Cloud API (requires API credentials)")
    print("=" * 70)


def main():
    """Main function"""
    import sys
    
    # Device info from test results
    lamp_ip = "YOUR_DEVICE_IP"
    lamp_id = "YOUR_DEVICE_ID"
    version = "3.5"
    
    if len(sys.argv) > 1:
        lamp_ip = sys.argv[1]
    if len(sys.argv) > 2:
        lamp_id = sys.argv[2]
    if len(sys.argv) > 3:
        version = sys.argv[3]
    
    print(f"\nUsing device: {lamp_id} @ {lamp_ip} (v{version})\n")
    
    diagnose_lamp_connection(lamp_ip, lamp_id, version)


if __name__ == "__main__":
    main()
