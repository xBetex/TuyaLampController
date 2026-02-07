#!/usr/bin/env python3
"""
Test the main application with color map window
"""

import tkinter as tk


def test_main_application():
    """Test main app directly"""
    print("Testing main application...")

    root = tk.Tk()
    root.withdraw()  # Hide main window

    try:
        from improved_lamp_controller import ImprovedLampController

        # Create the main controller
        controller = ImprovedLampController(root)

        # Test if it can open color map
        print("✅ Testing color map window...")
        controller.open_color_map_window()

        # Schedule close after 5 seconds
        root.after(5000, root.destroy)

        print("✅ Color map window test completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        root.after(2000, root.destroy)


if __name__ == "__main__":
    test_main_application()
