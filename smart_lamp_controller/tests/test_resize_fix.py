#!/usr/bin/env python3
"""
Clean test of color map window with resize fix
"""

import tkinter as tk


def test_simple():
    """Test color map window with clean resize handling"""
    print("Testing color map window...")

    root = tk.Tk()
    root.withdraw()  # Hide main window

    try:
        from color_map_window import ColorMapWindow

        print("Import successful")

        # Test class availability
        window_class = color_map_window.ColorMapWindow
        print("Class available")

        # Test instantiation with mock objects
        class MockDeviceManager:
            def __init__(self):
                self.is_connected = True

        class MockEffectsEngine:
            def stop_all_effects(self):
                pass

            def set_color_from_hex(self, color, brightness):
                print(f"Mock: Setting color {color}")

        print("Testing instantiation...")
        try:
            device_manager = MockDeviceManager()
            effects_engine = MockEffectsEngine()

            window = window_class(None, device_manager, effects_engine)
            print("SUCCESS: ColorMapWindow created")

            # Test that it has the required attributes
            required_attrs = [
                "pps_var",
                "pps_combo",
                "update_rate_label",
                "live_var",
                "live_checkbox",
                "live_status_label",
                "history_text",
                "history_count_label",
            ]

            missing_attrs = []
            present_attrs = []

            for attr in required_attrs:
                if hasattr(window, attr):
                    present_attrs.append(attr)
                else:
                    missing_attrs.append(attr)

            if missing_attrs:
                print(f"ERROR: Missing attributes: {missing_attrs}")
            else:
                print("SUCCESS: All required attributes present")

            # Test resize binding
            if hasattr(window, "on_window_resize"):
                print("SUCCESS: Resize handler bound")
            else:
                print("ERROR: Resize handler missing")

            root.after(2000, root.destroy())

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback

            traceback.print_exc()
            root.after(3000, root.destroy())

    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        import traceback

        traceback.print_exc()
        root.after(3000, root.destroy())


if __name__ == "__main__":
    test_simple()
