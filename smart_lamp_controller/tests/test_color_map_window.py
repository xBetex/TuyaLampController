#!/usr/bin/env python3
"""
Test Color Map Window - Test the new separate color map window
"""

import tkinter as tk
from tkinter import ttk

def test_color_map_window():
    """Test the color map window"""
    
    # Create main window
    root = tk.Tk()
    root.title("Color Map Window Test")
    root.geometry("400x300")
    
    # Mock device manager and effects engine
    class MockDeviceManager:
        def __init__(self):
            self.is_connected = True
    
    class MockEffectsEngine:
        def stop_all_effects(self):
            print("Mock: Stopping all effects")
        
        def set_color_from_hex(self, color, brightness):
            print(f"Mock: Setting color to {color} with brightness {brightness}")
    
    device_manager = MockDeviceManager()
    effects_engine = MockEffectsEngine()
    
    # Create test UI
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(
        main_frame,
        text="Color Map Window Test",
        font=("Segoe UI", 14, "bold")
    ).pack(pady=(0, 20))
    
    ttk.Label(
        main_frame,
        text="Click the button below to open the color map window",
        font=("Segoe UI", 10)
    ).pack(pady=(0, 20))
    
    def open_color_map():
        try:
            from color_map_window import open_color_map_window
            open_color_map_window(root, device_manager, effects_engine)
            print("Color map window opened successfully")
        except Exception as e:
            print(f"Error opening color map window: {e}")
            import traceback
            traceback.print_exc()
    
    ttk.Button(
        main_frame,
        text="Open Color Map Window",
        command=open_color_map
    ).pack(pady=10)
    
    # Status
    try:
        from color_selection_logic import SCREEN_CAPTURE_AVAILABLE
        if SCREEN_CAPTURE_AVAILABLE:
            status_text = "✅ All dependencies available"
            status_color = "green"
        else:
            status_text = "⚠️ Install: pip install mss pillow numpy"
            status_color = "orange"
    except ImportError:
        status_text = "❌ Color selection module not found"
        status_color = "red"
    
    ttk.Label(
        main_frame,
        text=status_text,
        foreground=status_color,
        font=("Segoe UI", 9)
    ).pack(pady=(20, 0))
    
    print("Starting color map window test...")
    print("Dependencies check:")
    
    try:
        import mss
        print("✅ mss available")
    except ImportError:
        print("❌ mss not available - pip install mss")
    
    try:
        from PIL import Image, ImageTk
        print("✅ PIL available")
    except ImportError:
        print("❌ PIL not available - pip install pillow")
    
    try:
        import numpy as np
        print("✅ numpy available")
    except ImportError:
        print("❌ numpy not available - pip install numpy")
    
    root.mainloop()

if __name__ == "__main__":
    test_color_map_window()