"""Debug script to test Tuya device connection."""
import tinytuya
import json
import socket

# Device credentials from API response
DEVICE_ID = "eb3c5109e4834e0442in3u"
LOCAL_KEY = "V#F/0^-*FOxL2u+G"
CONFIGURED_IP = "192.168.15.30"

def scan_network():
    """Scan for Tuya devices on the network."""
    print("\n=== Scanning for Tuya devices on network ===")
    print("This may take 10-20 seconds...\n")
    devices = tinytuya.deviceScan(verbose=True)
    return devices

def test_connection(ip, version="3.5"):
    """Test connection with specific IP and version."""
    print(f"\n=== Testing connection to {ip} with version {version} ===")

    device = tinytuya.BulbDevice(
        dev_id=DEVICE_ID,
        address=ip,
        local_key=LOCAL_KEY,
        version=version
    )
    device.set_socketTimeout(5)

    try:
        status = device.status()
        print(f"SUCCESS! Status: {json.dumps(status, indent=2)}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def check_ip_reachable(ip):
    """Check if IP is reachable."""
    print(f"\n=== Checking if {ip} is reachable ===")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, 6668))  # Tuya default port
        sock.close()
        if result == 0:
            print(f"Port 6668 is OPEN on {ip}")
            return True
        else:
            print(f"Port 6668 is CLOSED on {ip}")
            return False
    except Exception as e:
        print(f"Error checking port: {e}")
        return False

def main():
    print("=" * 60)
    print("TUYA DEVICE CONNECTION DEBUG")
    print("=" * 60)
    print(f"Device ID: {DEVICE_ID}")
    print(f"Local Key: {LOCAL_KEY}")
    print(f"Configured IP: {CONFIGURED_IP}")

    # Step 1: Check if configured IP is reachable
    reachable = check_ip_reachable(CONFIGURED_IP)

    # Step 2: Try different protocol versions
    if reachable:
        print("\n=== Testing different protocol versions ===")
        for version in ["3.5", "3.4", "3.3", "3.1"]:
            if test_connection(CONFIGURED_IP, version):
                print(f"\n*** Working version found: {version} ***")
                break
    else:
        print(f"\nDevice not reachable at {CONFIGURED_IP}")
        print("The device IP may have changed. Running network scan...")

    # Step 3: Scan network to find actual device IP
    print("\n" + "=" * 60)
    response = input("Run network scan to find device? (y/n): ")
    if response.lower() == 'y':
        devices = scan_network()

        if devices:
            print("\n=== Found devices ===")
            for ip, dev in devices.items():
                print(f"\nIP: {ip}")
                print(f"  ID: {dev.get('gwId', 'unknown')}")
                print(f"  Version: {dev.get('version', 'unknown')}")

                # If we found our device, try to connect
                if dev.get('gwId') == DEVICE_ID:
                    print(f"\n*** Found your device at {ip}! ***")
                    detected_version = dev.get('version', '3.5')
                    test_connection(ip, detected_version)
                    print(f"\nUpdate your lamp_config.json with:")
                    print(f'  "address": "{ip}",')
                    print(f'  "version": "{detected_version}"')
        else:
            print("No devices found. Make sure:")
            print("  1. Your lamp is powered on")
            print("  2. Your computer is on the same WiFi network")
            print("  3. The lamp is connected to WiFi (not in pairing mode)")

if __name__ == "__main__":
    main()
