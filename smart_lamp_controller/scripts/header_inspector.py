#!/usr/bin/env python3
"""
HTTP Header Inspector for Smart Lamp
Captures and displays HTTP response headers and network statistics
"""

import requests
import socket
import subprocess
import platform
import json
from datetime import datetime
from urllib.parse import urlparse


class HeaderInspector:
    def __init__(self, lamp_ip=None, lamp_port=80):
        self.lamp_ip = lamp_ip
        self.lamp_port = lamp_port
        self.responses = []

    def inspect_http_headers(self, url, method="GET", headers=None, data=None):
        """Make HTTP request and capture response headers"""
        try:
            print(f"\n{'='*60}")
            print(f"🔍 Inspecting: {method} {url}")
            print(f"{'='*60}")
            
            # Make request
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, data=data, timeout=10, allow_redirects=False)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, data=data, timeout=10, allow_redirects=False)
            else:
                print(f"❌ Unsupported method: {method}")
                return None

            # Store response info
            response_info = {
                "url": url,
                "method": method,
                "timestamp": datetime.now().isoformat(),
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "request_headers": dict(response.request.headers) if hasattr(response, 'request') else {},
                "cookies": dict(response.cookies) if response.cookies else {},
                "content_length": len(response.content),
                "content_type": response.headers.get('Content-Type', 'Unknown'),
                "encoding": response.encoding,
            }

            # Display results
            print(f"\n📊 Response Status: {response.status_code} {response.reason}")
            print(f"\n📤 Request Headers:")
            print("-" * 60)
            for key, value in response_info["request_headers"].items():
                print(f"  {key}: {value}")

            print(f"\n📥 Response Headers:")
            print("-" * 60)
            for key, value in response_info["headers"].items():
                print(f"  {key}: {value}")

            if response_info["cookies"]:
                print(f"\n🍪 Cookies:")
                print("-" * 60)
                for key, value in response_info["cookies"].items():
                    print(f"  {key}: {value}")

            print(f"\n📦 Response Body Info:")
            print("-" * 60)
            print(f"  Content-Type: {response_info['content_type']}")
            print(f"  Content-Length: {response_info['content_length']} bytes")
            print(f"  Encoding: {response_info['encoding']}")
            
            # Show preview of response body
            if response_info['content_length'] > 0:
                preview = response.text[:500] if response.text else response.content[:500]
                print(f"\n📄 Response Preview (first 500 chars):")
                print("-" * 60)
                print(preview)
                if response_info['content_length'] > 500:
                    print(f"\n  ... (truncated, total {response_info['content_length']} bytes)")

            self.responses.append(response_info)
            return response_info

        except requests.exceptions.Timeout:
            print(f"❌ Request timeout for {url}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def get_network_connections(self, target_ip=None, target_port=None):
        """Get network connection statistics (netstat-like)"""
        print(f"\n{'='*60}")
        print(f"🌐 Network Connection Statistics")
        print(f"{'='*60}")

        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windows netstat
                cmd = ["netstat", "-an"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    connections = []
                    
                    for line in lines:
                        if 'ESTABLISHED' in line or 'LISTENING' in line or 'TIME_WAIT' in line:
                            parts = line.split()
                            if len(parts) >= 4:
                                proto = parts[0]
                                local_addr = parts[1]
                                foreign_addr = parts[2] if len(parts) > 2 else ""
                                state = parts[3] if len(parts) > 3 else ""
                                
                                # Filter by target if specified
                                if target_ip:
                                    if target_ip in local_addr or target_ip in foreign_addr:
                                        connections.append({
                                            "protocol": proto,
                                            "local": local_addr,
                                            "foreign": foreign_addr,
                                            "state": state
                                        })
                                elif target_port:
                                    if f":{target_port}" in local_addr or f":{target_port}" in foreign_addr:
                                        connections.append({
                                            "protocol": proto,
                                            "local": local_addr,
                                            "foreign": foreign_addr,
                                            "state": state
                                        })
                                else:
                                    connections.append({
                                        "protocol": proto,
                                        "local": local_addr,
                                        "foreign": foreign_addr,
                                        "state": state
                                    })
                    
                    if connections:
                        print(f"\n📡 Active Connections:")
                        print("-" * 60)
                        print(f"{'Protocol':<10} {'Local Address':<25} {'Foreign Address':<25} {'State':<15}")
                        print("-" * 60)
                        for conn in connections[:20]:  # Limit to 20 for readability
                            print(f"{conn['protocol']:<10} {conn['local']:<25} {conn['foreign']:<25} {conn['state']:<15}")
                        if len(connections) > 20:
                            print(f"\n  ... and {len(connections) - 20} more connections")
                    else:
                        filter_msg = f" matching {target_ip}:{target_port}" if target_ip or target_port else ""
                        print(f"ℹ️  No active connections{filter_msg}")
                else:
                    print(f"❌ Failed to get network statistics: {result.stderr}")
            
            else:
                # Linux/Mac netstat
                cmd = ["netstat", "-an"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print(result.stdout)
                else:
                    print(f"❌ Failed to get network statistics")

        except Exception as e:
            print(f"❌ Error getting network statistics: {e}")

    def scan_lamp_endpoints(self, lamp_ip, ports=[80, 443, 8080, 8888]):
        """Scan common HTTP endpoints on the lamp"""
        print(f"\n{'='*60}")
        print(f"🔍 Scanning HTTP Endpoints on {lamp_ip}")
        print(f"{'='*60}")

        common_paths = [
            "/",
            "/config",
            "/state",
            "/status",
            "/api/status",
            "/api/config",
            "/tuya",
            "/device",
            "/info",
        ]

        for port in ports:
            for path in common_paths:
                url = f"http://{lamp_ip}:{port}{path}"
                self.inspect_http_headers(url, method="GET")

    def save_results(self, filename="header_inspection_results.json"):
        """Save inspection results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(self.responses, f, indent=2)
            print(f"\n💾 Results saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

    def print_summary(self):
        """Print summary of all inspections"""
        print(f"\n{'='*60}")
        print(f"📋 Inspection Summary")
        print(f"{'='*60}")
        
        if not self.responses:
            print("No responses captured")
            return
        
        print(f"\nTotal requests: {len(self.responses)}")
        print(f"\nStatus Codes:")
        status_counts = {}
        for resp in self.responses:
            status = resp['status_code']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

        print(f"\nCommon Headers Found:")
        all_headers = set()
        for resp in self.responses:
            all_headers.update(resp['headers'].keys())
        
        for header in sorted(all_headers):
            print(f"  - {header}")


def main():
    """Main function for command-line usage"""
    import sys

    inspector = HeaderInspector()

    if len(sys.argv) > 1:
        lamp_ip = sys.argv[1]
        lamp_port = int(sys.argv[2]) if len(sys.argv) > 2 else 80

        print(f"🔍 HTTP Header Inspector for Lamp")
        print(f"Target: {lamp_ip}:{lamp_port}")
        
        # Get network connections
        inspector.get_network_connections(target_ip=lamp_ip, target_port=lamp_port)

        # Try common endpoints
        inspector.scan_lamp_endpoints(lamp_ip, ports=[lamp_port])

        # Print summary
        inspector.print_summary()

        # Save results
        inspector.save_results()

    else:
        print("Usage: python header_inspector.py <lamp_ip> [port]")
        print("\nExample:")
        print("  python header_inspector.py 192.168.1.100")
        print("  python header_inspector.py 192.168.1.100 80")
        print("\nOr use interactively:")
        print("  from header_inspector import HeaderInspector")
        print("  inspector = HeaderInspector('192.168.1.100')")
        print("  inspector.inspect_http_headers('http://192.168.1.100/')")


if __name__ == "__main__":
    main()
