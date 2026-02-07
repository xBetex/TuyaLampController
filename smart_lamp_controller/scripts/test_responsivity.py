#!/usr/bin/env python3
"""
Test lamp responsivity and response times
"""
import json
import time
import tinytuya
import statistics
from typing import List, Dict

class LampResponsivityTester:
    """Test lamp response times and functionality"""
    
    def __init__(self):
        # Load config
        with open('lamp_config.json', 'r') as f:
            config = json.load(f)
        
        self.device_config = config['device']
        self.device = None
        self.results = {}
        
    def connect(self) -> bool:
        """Connect to the lamp"""
        try:
            print(f"Connecting to {self.device_config['name']}...")
            self.device = tinytuya.BulbDevice(
                dev_id=self.device_config['id'],
                address=self.device_config['address'],
                local_key=self.device_config['local_key']
            )
            self.device.set_version(float(self.device_config['version']))
            
            # Test connection
            data = self.device.status()
            if 'Error' in str(data):
                print(f"❌ Connection failed: {data}")
                return False
            
            print("✅ Connected successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def measure_response_time(self, command_func, *args, **kwargs) -> float:
        """Measure response time for a command"""
        start_time = time.perf_counter()
        try:
            result = command_func(*args, **kwargs)
            end_time = time.perf_counter()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            if 'Error' in str(result):
                return -1  # Error
            
            return response_time
        except Exception:
            return -1  # Error
    
    def test_basic_commands(self) -> Dict[str, List[float]]:
        """Test basic command response times"""
        print("\n=== Testing Basic Commands ===")
        
        results = {
            'turn_on': [],
            'turn_off': [],
            'set_white': [],
            'set_color': [],
            'set_brightness': [],
            'status': []
        }
        
        # Test each command multiple times
        for i in range(5):
            print(f"Test run {i+1}/5...")
            
            # Turn on
            time.sleep(0.5)
            response_time = self.measure_response_time(self.device.turn_on)
            if response_time > 0:
                results['turn_on'].append(response_time)
                print(f"  Turn ON: {response_time:.1f}ms")
            
            # Set white light
            time.sleep(0.5)
            response_time = self.measure_response_time(self.device.set_white, 500, 500)
            if response_time > 0:
                results['set_white'].append(response_time)
                print(f"  Set White: {response_time:.1f}ms")
            
            # Set color (red)
            time.sleep(0.5)
            response_time = self.measure_response_time(self.device.set_colour, 255, 0, 0)
            if response_time > 0:
                results['set_color'].append(response_time)
                print(f"  Set Color (Red): {response_time:.1f}ms")
            
            # Set brightness
            time.sleep(0.5)
            response_time = self.measure_response_time(self.device.set_value, '22', 800)
            if response_time > 0:
                results['set_brightness'].append(response_time)
                print(f"  Set Brightness: {response_time:.1f}ms")
            
            # Get status
            time.sleep(0.5)
            response_time = self.measure_response_time(self.device.status)
            if response_time > 0:
                results['status'].append(response_time)
                print(f"  Get Status: {response_time:.1f}ms")
            
            # Turn off
            time.sleep(0.5)
            response_time = self.measure_response_time(self.device.turn_off)
            if response_time > 0:
                results['turn_off'].append(response_time)
                print(f"  Turn OFF: {response_time:.1f}ms")
        
        return results
    
    def test_color_transitions(self) -> Dict[str, List[float]]:
        """Test color change response times"""
        print("\n=== Testing Color Transitions ===")
        
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green  
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (255, 255, 255), # White
            (0, 0, 0)       # Black (off)
        ]
        
        results = {'color_changes': []}
        
        print("Testing rapid color changes...")
        for i, (r, g, b) in enumerate(colors * 2):  # Test each color twice
            response_time = self.measure_response_time(self.device.set_colour, r, g, b)
            if response_time > 0:
                results['color_changes'].append(response_time)
                print(f"  Color {i+1} (RGB:{r},{g},{b}): {response_time:.1f}ms")
            time.sleep(0.2)  # Short delay between colors
        
        return results
    
    def test_rapid_commands(self) -> Dict[str, List[float]]:
        """Test rapid successive commands"""
        print("\n=== Testing Rapid Commands ===")
        
        results = {'rapid_commands': []}
        
        print("Testing 20 rapid brightness changes...")
        for i in range(20):
            brightness = 100 + (i * 40) % 900  # Cycle through brightness values
            response_time = self.measure_response_time(self.device.set_value, '22', brightness)
            if response_time > 0:
                results['rapid_commands'].append(response_time)
                print(f"  Brightness {brightness}: {response_time:.1f}ms")
        
        return results
    
    def analyze_results(self, results: Dict[str, List[float]]):
        """Analyze and display test results"""
        print("\n" + "="*50)
        print("RESPONSIVITY ANALYSIS")
        print("="*50)
        
        for test_name, times in results.items():
            if not times:
                print(f"\n{test_name}: No successful measurements")
                continue
            
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            print(f"\n{test_name.upper()}:")
            print(f"  Average: {avg_time:.1f}ms")
            print(f"  Min: {min_time:.1f}ms")
            print(f"  Max: {max_time:.1f}ms")
            print(f"  Std Dev: {std_dev:.1f}ms")
            print(f"  Success Rate: {len(times)}/5 tests ({len(times)*20}%)")
        
        # Overall assessment
        all_times = []
        for times in results.values():
            all_times.extend(times)
        
        if all_times:
            overall_avg = statistics.mean(all_times)
            print(f"\nOVERALL PERFORMANCE:")
            print(f"  Average Response Time: {overall_avg:.1f}ms")
            
            if overall_avg < 100:
                print("  🟢 EXCELLENT: Very responsive")
            elif overall_avg < 200:
                print("  🟡 GOOD: Acceptable responsiveness")
            elif overall_avg < 500:
                print("  🟠 FAIR: Some delay noticeable")
            else:
                print("  🔴 POOR: Significant delays")
    
    def run_full_test(self):
        """Run complete responsivity test"""
        print("🔬 LAMP RESPONSIVITY TEST")
        print("="*50)
        
        if not self.connect():
            return
        
        print("\nStarting tests... (lamp will flash and change colors)")
        print("Make sure you can see the lamp clearly!")
        
        try:
            # Run all tests
            basic_results = self.test_basic_commands()
            color_results = self.test_color_transitions()
            rapid_results = self.test_rapid_commands()
            
            # Combine all results
            all_results = {**basic_results, **color_results, **rapid_results}
            
            # Analyze results
            self.analyze_results(all_results)
            
            # Final status check
            print("\nFinal device status:")
            final_status = self.device.status()
            print(json.dumps(final_status, indent=2))
            
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
        except Exception as e:
            print(f"\nTest error: {e}")
        
        print("\n✅ Responsivity test completed!")

def main():
    """Main function"""
    tester = LampResponsivityTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
