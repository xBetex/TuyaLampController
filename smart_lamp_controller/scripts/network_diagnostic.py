#!/usr/bin/env python3
"""
Network Diagnostic Tool for Smart Lamp Controller
"""

import socket
import subprocess
import platform
import ipaddress
import threading
import time


def get_local_ip():
    """Get local IP addresses"""
    try:
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        return local_ips
    except:
        return []


def scan_network(ip_range):
    """Simple network scanner"""
    active_hosts = []

    def ping_host(ip):
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", "100", ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", ip]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                active_hosts.append(ip)
        except:
            pass

    threads = []
    for ip in ip_range:
        thread = threading.Thread(target=ping_host, args=(ip,))
        thread.start()
        threads.append(thread)
        time.sleep(0.01)  # Small delay to avoid flooding

    for thread in threads:
        thread.join()

    return active_hosts


def get_network_range(ip):
    """Get network range from IP"""
    try:
        network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
        return [str(host) for host in network.hosts()]
    except:
        return []


def check_tuya_ports(ip):
    """Check if Tuya ports are open on device"""
    tuya_ports = [6668, 9999, 1883, 443]
    open_ports = []

    for port in tuya_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
        except:
            pass
        finally:
            sock.close()

    return open_ports


def main():
    print("🔍 Smart Lamp Network Diagnostic Tool")
    print("=" * 50)

    # Get local IPs
    local_ips = get_local_ip()
    print(f"\n📱 Local IP Addresses:")
    for ip in local_ips:
        print(f"  - {ip}")

    if not local_ips:
        print("❌ Could not determine local IP addresses")
        return

    # Use first IP for network scan
    base_ip = local_ips[0]
    network_range = get_network_range(base_ip)

    print(f"\n🌐 Network Range: {base_ip}/24")
    print(f"📡 Scanning network for active hosts...")

    active_hosts = scan_network(network_range[:50])  # Limit scan for speed

    print(f"✅ Found {len(active_hosts)} active hosts:")
    for host in active_hosts:
        print(f"  - {host}")

        # Check for Tuya ports
        open_ports = check_tuya_ports(host)
        if open_ports:
            print(f"    🔌 Open Tuya ports: {open_ports}")

    # Network recommendations
    print(f"\n💡 Network Recommendations:")
    if len(active_hosts) < 5:
        print(
            "  - Few hosts found. Your WiFi and Ethernet might be on different subnets."
        )
        print("  - Check router settings for 'AP Isolation' or 'Client Isolation'")
        print("  - Consider bridging network connections in Windows")

    # Try to find Tuya devices specifically
    print(f"\n🔍 Attempting to discover Tuya devices...")
    try:
        import tinytuya

        devices = tinytuya.deviceScan()
        if devices:
            print("✅ Tuya devices found:")
            for ip, info in devices.items():
                print(f"  - IP: {ip}, ID: {info.get('gwId', 'Unknown')}")
        else:
            print("❌ No Tuya devices found via scan")
    except Exception as e:
        print(f"❌ Tuya scan failed: {e}")


if __name__ == "__main__":
    main()
