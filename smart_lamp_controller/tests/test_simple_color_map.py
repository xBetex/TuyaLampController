#!/usr/bin/env python3
"""
Simple test of color map window only
"""

import tkinter as tk


def test_simple():
    """Test color map window directly"""
    root = tk.Tk()
    root.withdraw()

    print("Testing color map window functionality...")

    try:
        # Direct import test
        print("Testing import...")
        import color_map_window

        print("OK: color_map_window imported successfully")

        # Test class availability
        print("Testing ColorMapWindow class...")
        window_class = color_map_window.ColorMapWindow
        print("OK: ColorMapWindow class available")

        # Test instantiation with mock objects
        class MockDeviceManager:
            def __init__(self):
                self.is_connected = True

        class MockEffectsEngine:
            def stop_all_effects(self):
                pass

            def set_color_from_hex(self, color, brightness):
                print(f"Mock: Setting color {color}")

        print("Testing ColorMapWindow instantiation...")
        try:
            window = window_class(None, MockDeviceManager(), MockEffectsEngine())
            print("OK: ColorMapWindow created successfully")

            # Check for rate control attributes
            attrs = ["pps_var", "pps_combo", "update_rate_label"]
            for attr in attrs:
                if hasattr(window, attr):
                    print(f"OK: {attr} attribute exists")
                else:
                    print(f"ERROR: {attr} attribute missing")

            root.after(2000, root.destroy())

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback

            traceback.print_exc()
            root.after(3000, root.destroy())

    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback

        traceback.print_exc()
        root.after(3000, root.destroy())


if __name__ == "__main__":
    test_simple()
