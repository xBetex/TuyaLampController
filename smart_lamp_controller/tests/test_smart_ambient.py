#!/usr/bin/env python3
"""
Test script for Smart Ambient functionality
"""

import time
import logging
from smart_ambient_processor import SmartAmbientProcessor
from color_selection_logic import SCREEN_CAPTURE_AVAILABLE

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_color_callback(hex_color):
    """Test callback for color updates"""
    print(f"🎯 Color selected: {hex_color}")

def test_status_callback(status):
    """Test callback for status updates"""
    print(f"📊 Status: {status}")

def main():
    print("Testing Smart Ambient Processor...")
    print(f"Screen capture available: {SCREEN_CAPTURE_AVAILABLE}")
    
    if not SCREEN_CAPTURE_AVAILABLE:
        print("❌ Screen capture dependencies not available")
        print("Install with: pip install mss pillow numpy")
        return
    
    # Create processor
    processor = SmartAmbientProcessor()
    
    # Test parameters
    processor.set_monitor(1)  # Primary monitor
    processor.set_update_interval(2.0)  # 2 second updates for testing
    
    print("Starting Smart Ambient processor for 10 seconds...")
    
    # Start processing
    success = processor.start(test_color_callback, test_status_callback)
    
    if not success:
        print("❌ Failed to start processor")
        return
    
    # Run for 10 seconds
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
    
    # Stop processing
    processor.stop()
    print("✅ Test completed")

if __name__ == "__main__":
    main()