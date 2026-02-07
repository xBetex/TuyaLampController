#!/usr/bin/env python3
"""
Find the local IP address of the Tuya lamp
"""
import tinytuya
import socket
import subprocess
import re
import sys

def get_network_range():
    """Get the local network range"""
    try:
        # Get local IP and subnet
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Extract network portion (first 3 octets)
        if '.' in local_ip:
            parts = local_ip.split('.')
            network_base = f"{parts[0]}.{parts[1]}.{parts[2]}"
            return network_base
        return "192.168.1"  # Default fallback
        
    except Exception:
        return "192.168.1"  # Default fallback

def scan_network(network_base):
    """Scan the network for Tuya devices"""
    print(f"Scanning network {network_base}.x for Tuya devices...")
    
    # Try to discover devices
    devices = tinytuya.deviceScan()
    
    if devices:
        print(f"Found {len(devices)} devices:")
        for ip, info in devices.items():
            print(f"  IP: {ip}")
            print(f"  ID: {info.get('gwId', 'Unknown')}")
            print(f"  Product: {info.get('productKey', 'Unknown')}")
            print()
        return devices
    
    return {}

def test_device_connection(device_id, ip, local_key):
    """Test connection to a specific device"""
    print(f"Testing connection to {device_id} at {ip}...")
    
    try:
        device = tinytuya.BulbDevice(
            dev_id=device_id,
            address=ip,
            local_key=local_key
        )
        device.set_version(3.5)
        
        # Test connection
        data = device.status()
        
        if 'Error' in str(data):
            print(f"❌ Connection failed: {data}")
            return False
        else:
            print("✅ Connection successful!")
            print(f"Device status: {data}")
            return True
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main function"""
    device_id = "YOUR_DEVICE_ID"
    local_key = "YOUR_LOCAL_KEY"
    
    print("=== Smart Lamp Local IP Finder ===\n")
    
    # Get network range
    network_base = get_network_range()
    print(f"Your network appears to be: {network_base}.x")
    
    # Scan for devices
    devices = scan_network(network_base)
    
    if not devices:
        print("No devices found via automatic scan.")
        print("Trying common IP addresses...")
        
        # Try common IPs
        common_ips = [
            f"{network_base}.1",
            f"{network_base}.10", 
            f"{network_base}.30",
            f"{network_base}.100",
            f"{network_base}.254"
        ]
        
        for ip in common_ips:
            print(f"\nTrying {ip}...")
            if test_device_connection(device_id, ip, local_key):
                print(f"\n✅ SUCCESS! Device found at: {ip}")
                print("Update your lamp_config.json with this IP address.")
                return ip
        
        print("\n❌ Could not find device on common IPs.")
        return None
    
    else:
        # Test each found device
        for ip, info in devices.items():
            found_id = info.get('gwId', '')
            if found_id == device_id:
                print(f"Found matching device at {ip}!")
                if test_device_connection(device_id, ip, local_key):
                    print(f"\n✅ SUCCESS! Device confirmed at: {ip}")
                    print("Update your lamp_config.json with this IP address.")
                    return ip
        
        print("\n❌ Found devices but none matched your device ID.")
        return None

if __name__ == "__main__":
    main()
