#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full Lamp Test Suite
Comprehensive testing of lamp communication including HTTP headers, network stats, and protocols
"""

import sys
import os
import time
import socket
import requests
from datetime import datetime
from header_inspector import HeaderInspector

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import tinytuya
    TINYTUYA_AVAILABLE = True
except ImportError:
    TINYTUYA_AVAILABLE = False
    print("⚠️  tinytuya not available - some tests will be skipped")


class FullLampTest:
    def __init__(self, lamp_ip=None):
        self.lamp_ip = lamp_ip
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "lamp_ip": lamp_ip,
            "tests": []
        }
        self.inspector = HeaderInspector(lamp_ip) if lamp_ip else HeaderInspector()

    def log_test(self, test_name, status, details=None, error=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "SKIP", "WARN"
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": str(error) if error else None
        }
        self.test_results["tests"].append(result)
        
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️",
            "WARN": "⚠️"
        }.get(status, "❓")
        
        print(f"{status_icon} {test_name}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
        if error:
            print(f"   Error: {error}")
        print()

    def test_network_connectivity(self):
        """Test 1: Basic network connectivity"""
        print("=" * 70)
        print("TEST 1: Network Connectivity")
        print("=" * 70)
        
        if not self.lamp_ip:
            self.log_test("Network Connectivity", "SKIP", {"reason": "No lamp IP provided"})
            return False
        
        try:
            # Ping test
            import subprocess
            import platform
            
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", "1000", self.lamp_ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "1", self.lamp_ip]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            ping_success = result.returncode == 0
            
            # Port scan
            common_ports = [80, 443, 6668, 6667, 9999, 1883, 8080]
            open_ports = []
            
            for port in common_ports:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                try:
                    result = sock.connect_ex((self.lamp_ip, port))
                    if result == 0:
                        open_ports.append(port)
                except:
                    pass
                finally:
                    sock.close()
            
            details = {
                "ping": "OK" if ping_success else "FAILED",
                "open_ports": open_ports if open_ports else "None found"
            }
            
            if ping_success or open_ports:
                self.log_test("Network Connectivity", "PASS", details)
                return True
            else:
                self.log_test("Network Connectivity", "FAIL", details)
                return False
                
        except Exception as e:
            self.log_test("Network Connectivity", "FAIL", error=e)
            return False

    def test_http_endpoints(self):
        """Test 2: HTTP endpoint discovery and header inspection"""
        print("=" * 70)
        print("TEST 2: HTTP Endpoint Discovery")
        print("=" * 70)
        
        if not self.lamp_ip:
            self.log_test("HTTP Endpoints", "SKIP", {"reason": "No lamp IP provided"})
            return
        
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
            "/json",
            "/api",
        ]
        
        common_ports = [80, 443, 8080, 8888]
        successful_endpoints = []
        
        for port in common_ports:
            for path in common_paths:
                url = f"http://{self.lamp_ip}:{port}{path}"
                try:
                    response = requests.get(url, timeout=3, allow_redirects=False)
                    
                    if response.status_code < 500:  # Any response is interesting
                        successful_endpoints.append({
                            "url": url,
                            "status": response.status_code,
                            "content_type": response.headers.get('Content-Type', 'Unknown'),
                            "content_length": len(response.content)
                        })
                        
                        # Log headers for successful endpoints
                        print(f"\n✅ Found endpoint: {url}")
                        print(f"   Status: {response.status_code}")
                        print(f"   Headers:")
                        for key, value in response.headers.items():
                            print(f"     {key}: {value}")
                        
                        # Inspect with full header inspector
                        self.inspector.inspect_http_headers(url, method="GET")
                        
                except requests.exceptions.Timeout:
                    pass
                except requests.exceptions.ConnectionError:
                    pass
                except Exception as e:
                    pass
        
        if successful_endpoints:
            self.log_test("HTTP Endpoints", "PASS", {
                "found": len(successful_endpoints),
                "endpoints": successful_endpoints
            })
        else:
            self.log_test("HTTP Endpoints", "WARN", {
                "found": 0,
                "note": "No HTTP endpoints responded. Lamp may use TCP protocol only."
            })

    def test_tuya_discovery(self):
        """Test 3: Tuya device discovery"""
        print("=" * 70)
        print("TEST 3: Tuya Device Discovery")
        print("=" * 70)
        
        if not TINYTUYA_AVAILABLE:
            self.log_test("Tuya Discovery", "SKIP", {"reason": "tinytuya library not available"})
            return
        
        try:
            devices = tinytuya.deviceScan()
            
            if devices:
                device_list = []
                for ip, info in devices.items():
                    device_info = {
                        "ip": ip,
                        "device_id": info.get("gwId", "Unknown"),
                        "version": info.get("version", "Unknown"),
                        "matches_target": ip == self.lamp_ip if self.lamp_ip else False
                    }
                    device_list.append(device_info)
                    
                    if self.lamp_ip and ip == self.lamp_ip:
                        print(f"\n✅ Found target device: {ip}")
                        print(f"   Device ID: {device_info['device_id']}")
                        print(f"   Version: {device_info['version']}")
                
                self.log_test("Tuya Discovery", "PASS", {
                    "devices_found": len(devices),
                    "devices": device_list
                })
            else:
                self.log_test("Tuya Discovery", "WARN", {
                    "devices_found": 0,
                    "note": "No Tuya devices found on network"
                })
                
        except Exception as e:
            self.log_test("Tuya Discovery", "FAIL", error=e)

    def test_tuya_connection(self):
        """Test 4: Tuya protocol connection"""
        print("=" * 70)
        print("TEST 4: Tuya Protocol Connection")
        print("=" * 70)
        
        if not TINYTUYA_AVAILABLE:
            self.log_test("Tuya Connection", "SKIP", {"reason": "tinytuya library not available"})
            return
        
        if not self.lamp_ip:
            self.log_test("Tuya Connection", "SKIP", {"reason": "No lamp IP provided"})
            return
        
        try:
            # Try to discover device first
            devices = tinytuya.deviceScan()
            device_id = None
            
            if devices and self.lamp_ip in devices:
                device_id = devices[self.lamp_ip].get("gwId")
                version = devices[self.lamp_ip].get("version", "3.1")
            else:
                # Try with a generic device ID
                device_id = "test_device"
                version = "3.1"
            
            if device_id:
                d = tinytuya.Device(device_id, self.lamp_ip)
                d.set_version(version)
                
                # Try to get status
                try:
                    status = d.status()
                    self.log_test("Tuya Connection", "PASS", {
                        "device_id": device_id,
                        "version": version,
                        "status_keys": list(status.keys()) if status else []
                    })
                except Exception as e:
                    self.log_test("Tuya Connection", "WARN", {
                        "device_id": device_id,
                        "note": "Device found but status query failed",
                        "error": str(e)
                    })
            else:
                self.log_test("Tuya Connection", "SKIP", {
                    "reason": "Could not determine device ID"
                })
                
        except Exception as e:
            self.log_test("Tuya Connection", "FAIL", error=e)

    def test_network_statistics(self):
        """Test 5: Network connection statistics"""
        print("=" * 70)
        print("TEST 5: Network Connection Statistics")
        print("=" * 70)
        
        if not self.lamp_ip:
            self.log_test("Network Statistics", "SKIP", {"reason": "No lamp IP provided"})
            return
        
        try:
            self.inspector.get_network_connections(target_ip=self.lamp_ip)
            self.log_test("Network Statistics", "PASS", {
                "note": "Network statistics displayed above"
            })
        except Exception as e:
            self.log_test("Network Statistics", "WARN", error=e)

    def test_http_methods(self):
        """Test 6: Different HTTP methods"""
        print("=" * 70)
        print("TEST 6: HTTP Methods Testing")
        print("=" * 70)
        
        if not self.lamp_ip:
            self.log_test("HTTP Methods", "SKIP", {"reason": "No lamp IP provided"})
            return
        
        methods_tested = []
        base_url = f"http://{self.lamp_ip}"
        
        for method in ["GET", "POST", "PUT", "OPTIONS", "HEAD"]:
            try:
                if method == "GET":
                    response = requests.get(base_url, timeout=3)
                elif method == "POST":
                    response = requests.post(base_url, timeout=3)
                elif method == "PUT":
                    response = requests.put(base_url, timeout=3)
                elif method == "OPTIONS":
                    response = requests.options(base_url, timeout=3)
                elif method == "HEAD":
                    response = requests.head(base_url, timeout=3)
                
                methods_tested.append({
                    "method": method,
                    "status": response.status_code,
                    "allowed": response.status_code != 405
                })
                
            except requests.exceptions.RequestException:
                methods_tested.append({
                    "method": method,
                    "status": "N/A",
                    "allowed": False
                })
        
        allowed_methods = [m["method"] for m in methods_tested if m["allowed"]]
        
        self.log_test("HTTP Methods", "PASS" if allowed_methods else "WARN", {
            "methods_tested": methods_tested,
            "allowed_methods": allowed_methods if allowed_methods else "None"
        })

    def test_response_headers_analysis(self):
        """Test 7: Detailed response headers analysis"""
        print("=" * 70)
        print("TEST 7: Response Headers Analysis")
        print("=" * 70)
        
        if not self.lamp_ip:
            self.log_test("Headers Analysis", "SKIP", {"reason": "No lamp IP provided"})
            return
        
        # Try to get a response first
        try:
            response = requests.get(f"http://{self.lamp_ip}", timeout=3)
            
            headers_analysis = {
                "total_headers": len(response.headers),
                "server": response.headers.get("Server", "Not specified"),
                "content_type": response.headers.get("Content-Type", "Not specified"),
                "content_length": response.headers.get("Content-Length", "Not specified"),
                "cache_control": response.headers.get("Cache-Control", "Not specified"),
                "connection": response.headers.get("Connection", "Not specified"),
                "all_headers": dict(response.headers)
            }
            
            print(f"\n📊 Headers Analysis:")
            print(f"   Total Headers: {headers_analysis['total_headers']}")
            print(f"   Server: {headers_analysis['server']}")
            print(f"   Content-Type: {headers_analysis['content_type']}")
            print(f"   Content-Length: {headers_analysis['content_length']}")
            print(f"\n   All Headers:")
            for key, value in headers_analysis['all_headers'].items():
                print(f"     {key}: {value}")
            
            self.log_test("Headers Analysis", "PASS", headers_analysis)
            
        except Exception as e:
            self.log_test("Headers Analysis", "WARN", {
                "note": "Could not retrieve headers",
                "error": str(e)
            })

    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 70)
        print("🚀 FULL LAMP TEST SUITE")
        print("=" * 70)
        print(f"Target: {self.lamp_ip if self.lamp_ip else 'Auto-discover'}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")
        
        start_time = time.time()
        
        # Run all tests
        self.test_network_connectivity()
        time.sleep(0.5)
        
        self.test_http_endpoints()
        time.sleep(0.5)
        
        self.test_tuya_discovery()
        time.sleep(0.5)
        
        self.test_tuya_connection()
        time.sleep(0.5)
        
        self.test_network_statistics()
        time.sleep(0.5)
        
        self.test_http_methods()
        time.sleep(0.5)
        
        self.test_response_headers_analysis()
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results["tests"])
        passed = sum(1 for t in self.test_results["tests"] if t["status"] == "PASS")
        failed = sum(1 for t in self.test_results["tests"] if t["status"] == "FAIL")
        warnings = sum(1 for t in self.test_results["tests"] if t["status"] == "WARN")
        skipped = sum(1 for t in self.test_results["tests"] if t["status"] == "SKIP")
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"⏱️  Duration: {elapsed_time:.2f} seconds")
        print("=" * 70)
        
        # Save results
        import json
        filename = f"lamp_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Full results saved to: {filename}")
        
        return self.test_results


def discover_lamp_ip():
    """Try to discover lamp IP automatically"""
    print("🔍 Attempting to discover lamp IP...")
    
    # Try Tuya discovery
    if TINYTUYA_AVAILABLE:
        try:
            devices = tinytuya.deviceScan()
            if devices:
                print(f"✅ Found {len(devices)} Tuya device(s):")
                for ip, info in devices.items():
                    print(f"   - {ip} (ID: {info.get('gwId', 'Unknown')})")
                # Return first device IP
                return list(devices.keys())[0]
        except:
            pass
    
    return None


def main():
    """Main function"""
    lamp_ip = None
    
    if len(sys.argv) > 1:
        lamp_ip = sys.argv[1]
    else:
        # Try to discover
        lamp_ip = discover_lamp_ip()
        
        if not lamp_ip:
            print("❌ Could not auto-discover lamp IP")
            print("\nUsage: python full_lamp_test.py [lamp_ip]")
            print("\nExample:")
            print("  python full_lamp_test.py 192.168.1.100")
            print("\nOr let it auto-discover:")
            print("  python full_lamp_test.py")
            sys.exit(1)
    
    # Run full test suite
    tester = FullLampTest(lamp_ip)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
