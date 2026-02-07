#!/usr/bin/env python3
"""
Quick script to inspect HTTP headers from your lamp
Usage: python inspect_lamp_headers.py <lamp_ip> [port]
"""

import sys
from header_inspector import HeaderInspector


def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_lamp_headers.py <lamp_ip> [port]")
        print("\nExample:")
        print("  python inspect_lamp_headers.py 192.168.1.100")
        print("  python inspect_lamp_headers.py 192.168.1.100 80")
        sys.exit(1)

    lamp_ip = sys.argv[1]
    lamp_port = int(sys.argv[2]) if len(sys.argv) > 2 else 80

    print(f"🔍 Inspecting HTTP Headers from Lamp")
    print(f"📍 Target: {lamp_ip}:{lamp_port}")
    print(f"{'='*60}\n")

    inspector = HeaderInspector(lamp_ip, lamp_port)

    # First, show network connections
    inspector.get_network_connections(target_ip=lamp_ip, target_port=lamp_port)

    # Try common HTTP endpoints
    print(f"\n{'='*60}")
    print(f"🌐 Testing HTTP Endpoints")
    print(f"{'='*60}")

    common_urls = [
        f"http://{lamp_ip}:{lamp_port}/",
        f"http://{lamp_ip}:{lamp_port}/config",
        f"http://{lamp_ip}:{lamp_port}/state",
        f"http://{lamp_ip}:{lamp_port}/status",
        f"http://{lamp_ip}:{lamp_port}/api/status",
        f"http://{lamp_ip}:{lamp_port}/tuya",
        f"http://{lamp_ip}:{lamp_port}/device",
    ]

    for url in common_urls:
        inspector.inspect_http_headers(url, method="GET")
        print()  # Add spacing between requests

    # Print summary
    inspector.print_summary()

    # Save results
    inspector.save_results(f"lamp_headers_{lamp_ip.replace('.', '_')}.json")

    print(f"\n✅ Inspection complete!")
    print(f"📄 Results saved to: lamp_headers_{lamp_ip.replace('.', '_')}.json")


if __name__ == "__main__":
    main()
