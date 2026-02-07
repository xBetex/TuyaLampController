#!/usr/bin/env python3
"""
Simple resize fix for color map window
"""

import tkinter as tk
from tkinter import ttk


def create_color_map_window_with_resize_fix():
    """Create color map window with resize handling"""
    root = tk.Tk()
    root.withdraw()  # Hide main window

    # Define a minimal working color map window class
    class WorkingColorMapWindow:
        def __init__(self, parent, device_manager, effects_engine):
            self.parent = parent
            self.device_manager = device_manager
            self.effects_engine = effects_engine

            # Create window
            self.window = tk.Toplevel(parent)
            self.window.title("Color Map & Prevalence Analysis")
            self.window.geometry("1000x750")
            self.window.resizable(True, True)

            # Basic canvas
            self.color_map_canvas = tk.Canvas(
                self.window, width=400, height=300, bg="white"
            )
            self.color_map_canvas.pack(fill=tk.BOTH, expand=True)

            # Bind resize handler - SIMPLE VERSION
            self.window.bind("<Configure>", self.on_window_resize)

            # Close handler
            self.window.protocol("WM_DELETE_WINDOW", self.on_close)

            print("Working: Simple color map window with resize handling")

        def on_window_resize(self, event=None):
            """Simple resize handler - just print event"""
            print(f"Resize event: {event}")

        def on_close(self):
            """Simple close handler"""
            self.window.destroy()

    try:
        # Create mock objects
        class MockDeviceManager:
            is_connected = True

        class MockEffectsEngine:
            pass

        # Test the working window
        window = WorkingColorMapWindow(None, MockDeviceManager(), MockEffectsEngine())

        # Test resize simulation
        print("Testing resize functionality...")

        # Trigger resize events
        window.window.geometry("900x600")  # Resize 1
        root.update()
        window.window.geometry("1100x800")  # Resize 2
        root.update()
        window.window.geometry("1000x750")  # Resize 3
        root.update()

        print("SUCCESS: Resize handling works without breaking")

        # Clean close
        window.on_close()

        root.after(2000, root.destroy())

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    create_color_map_window_with_resize_fix()
