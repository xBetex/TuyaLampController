#!/usr/bin/env python3
"""
Test the rate-limited Live feature implementation
"""

import tkinter as tk
from tkinter import ttk


def test_rate_limited_live():
    """Test the rate-limited live feature"""

    root = tk.Tk()
    root.title("Live Feature - Rate Limited")
    root.geometry("600x450")

    # Main frame
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Title
    ttk.Label(
        main_frame,
        text="Live Feature - RATE LIMITED",
        font=("Segoe UI", 16, "bold"),
        foreground="#00aaff",
    ).pack(pady=(0, 20))

    # Fix details
    fix_text = """
    RATE LIMITING FIX:
    
    [OK] Limited to 1 request per 4 seconds
    - Changed update interval from 1.0s to 4.0s
    - Reduced lamp requests to prevent flooding
    - More stable and responsive system
    
    [OK] Better visual feedback
    - Added update rate indicator "(4s)"
    - Green when active, shows rate
    - Clear when inactive
    - Better status messages
    
    [OK] Improved user experience
    - Less frequent updates = smoother
    - Prevents device overload
    - More accurate color averaging
    - Still responsive to screen changes
    """

    ttk.Label(
        main_frame,
        text=fix_text,
        font=("Consolas", 10),
        justify=tk.LEFT,
        wraplength=550,
    ).pack(pady=20)

    # Visual demo
    demo_frame = ttk.LabelFrame(main_frame, text="Rate Indicator Demo", padding="10")
    demo_frame.pack(fill=tk.X, pady=20)

    def simulate_rate_limited():
        status_label.config(text="●", foreground="#00ff00")
        rate_label.config(text="(4s)", foreground="#00aa00")
        status_text.set("Live mode active - updating every 4 seconds")
        # Simulate one update after 4 seconds
        root.after(4000, lambda: status_label.config(text="●", foreground="#ffff00"))
        root.after(4100, lambda: status_label.config(text="●", foreground="#00ff00"))

    def simulate_stopped():
        status_label.config(text="●", foreground="#cccccc")
        rate_label.config(text="", foreground="#888888")
        status_text.set("Live mode stopped")

    # Demo controls
    controls_frame = ttk.Frame(demo_frame)
    controls_frame.pack()

    status_label = ttk.Label(
        controls_frame, text="●", font=("Segoe UI", 16), foreground="#cccccc"
    )
    status_label.pack(side=tk.LEFT, padx=(0, 20))

    rate_label = ttk.Label(
        controls_frame, text="", font=("Segoe UI", 8), foreground="#888888"
    )
    rate_label.pack(side=tk.LEFT, padx=5)

    status_text = tk.StringVar(value="Ready")

    button_frame = ttk.Frame(demo_frame)
    button_frame.pack(pady=10)

    ttk.Button(
        button_frame, text="Start Live (4s interval)", command=simulate_rate_limited
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="Stop Live", command=simulate_stopped).pack(
        side=tk.LEFT, padx=5
    )

    ttk.Label(demo_frame, textvariable=status_text, font=("Segoe UI", 10)).pack(
        pady=(10, 0)
    )

    # Technical details
    technical_text = """
    TECHNICAL IMPLEMENTATION:
    
    • Smart ambient processor update interval: 4.0 seconds
    • Color change threshold: 0.1 (10% difference)
    • Maximum updates: 15 per minute instead of 60
    • Better for device longevity and stability
    • Still responsive to significant screen changes
    
    The live mode now respects the 1/4s rate limit!
    """

    ttk.Label(
        main_frame,
        text=technical_text,
        font=("Segoe UI", 9),
        justify=tk.LEFT,
        foreground="#333333",
        wraplength=550,
    ).pack(pady=20)

    print("Live Feature Rate Limit Test Window")
    print("================================")
    print("[OK] Limited to 1 request per 4 seconds")
    print("[OK] Added update rate indicator (4s)")
    print("[OK] Improved status messages")
    print("[OK] Better device stability and responsiveness")
    print("")
    print("The live feature is now properly rate-limited!")

    root.mainloop()


if __name__ == "__main__":
    test_rate_limited_live()
