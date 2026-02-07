#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guide: Finding Local Key in Device Information Page
"""

import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def show_where_to_find_key():
    """Show where to find the key in the device information page"""
    print("=" * 70)
    print("🔍 Finding Local Key in Device Information Page")
    print("=" * 70)
    
    print("\nYou're on the Device Information page, but the local_key is usually")
    print("in a DIFFERENT section. Here's where to look:\n")
    
    print("=" * 70)
    print("📍 WHERE TO LOOK")
    print("=" * 70)
    
    locations = [
        {
            "Location": "1. Security Settings Tab",
            "Instructions": [
                "Look for tabs at the top of the device page",
                "Click on 'Security' or 'Security Settings' tab",
                "Look for 'Local Key' or 'Device Secret' field"
            ]
        },
        {
            "Location": "2. Device Credentials Section",
            "Instructions": [
                "Scroll down on the Device Information page",
                "Look for 'Device Credentials' or 'Authentication' section",
                "The local_key should be there"
            ]
        },
        {
            "Location": "3. Advanced Settings",
            "Instructions": [
                "Look for 'Advanced' or 'More Settings' button/link",
                "Click to expand",
                "Find 'Local Key' field"
            ]
        },
        {
            "Location": "4. API Explorer (Alternative)",
            "Instructions": [
                "Go to: Cloud → API Explorer",
                "Select: Device Management → Query Device Details",
                "Enter Device ID: YOUR_DEVICE_ID",
                "Click 'Send Request'",
                "Look for 'local_key' in JSON response"
            ]
        },
        {
            "Location": "5. Device Debug Page",
            "Instructions": [
                "Go back to the device list/table",
                "Click 'Debug Device' in the Operation column",
                "Look for 'Local Key' on the debug page"
            ]
        }
    ]
    
    for loc in locations:
        print(f"\n{loc['Location']}:")
        for i, instruction in enumerate(loc['Instructions'], 1):
            print(f"   {i}. {instruction}")
    
    print("\n" + "=" * 70)
    print("💡 IMPORTANT NOTES")
    print("=" * 70)
    
    print("\n1. IP Address Difference:")
    print("   - Tuya shows: 179.117.65.210 (Public/WAN IP)")
    print("   - Local network: YOUR_DEVICE_IP (Local/LAN IP)")
    print("   - Use YOUR_DEVICE_IP for local control (this is correct!)")
    
    print("\n2. Key Format:")
    print("   - Usually 16 hexadecimal characters")
    print("   - Example: 'a1b2c3d4e5f6g7h8'")
    print("   - Sometimes labeled as 'Device Secret' instead of 'Local Key'")
    
    print("\n3. If You Still Can't Find It:")
    print("   - Some devices don't expose local_key in web interface")
    print("   - Try API Explorer method (Location 4 above)")
    print("   - Or use network packet capture")
    
    print("\n" + "=" * 70)
    print("🎯 RECOMMENDED: Try These in Order")
    print("=" * 70)
    print("\n1. Look for 'Security' or 'Security Settings' tab on the device page")
    print("2. Scroll down to find 'Device Credentials' section")
    print("3. Try API Explorer: Cloud → API Explorer → Query Device Details")
    print("4. Go back to device list and click 'Debug Device'")
    print("=" * 70 + "\n")


def show_api_explorer_method():
    """Show how to use API Explorer"""
    print("\n" + "=" * 70)
    print("🌐 Using API Explorer to Get Local Key")
    print("=" * 70)
    
    print("\nStep-by-step:")
    print("\n1. In Tuya IoT Platform, go to: Cloud → API Explorer")
    print("2. In the API dropdown, select:")
    print("   'Device Management' → 'Query Device Details'")
    print("3. In the parameters, enter:")
    print("   device_id: YOUR_DEVICE_ID")
    print("4. Click 'Send Request' or 'Execute'")
    print("5. Look at the JSON response for:")
    print("   - 'local_key'")
    print("   - 'localKey'")
    print("   - 'device_secret'")
    print("   - 'secret'")
    print("\n6. Copy the value (it's the local_key!)")
    print("=" * 70)


if __name__ == "__main__":
    show_where_to_find_key()
    show_api_explorer_method()
