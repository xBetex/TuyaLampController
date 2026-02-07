#!/usr/bin/env python3
"""
Scrollable Frame - Reusable scrollable container widget for tkinter
"""

import tkinter as tk
from tkinter import ttk


class ScrollableFrame(ttk.Frame):
    """
    A scrollable frame using Canvas and Scrollbar.
    Use scrollable_frame attribute to add widgets.
    """

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )

        # Create the scrollable frame inside the canvas
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure the scrollable frame to update the scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        # Add the frame to the canvas
        self.canvas_frame = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        # Configure canvas resizing
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Configure scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack everything
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        self.bind_mouse_wheel(self.canvas)
        self.bind_mouse_wheel(self.scrollable_frame)

    def _on_canvas_configure(self, event):
        """Update the width of the inner frame to match the canvas"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def bind_mouse_wheel(self, widget):
        """Recursively bind mouse wheel events to a widget and its children"""
        widget.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        widget.bind("<Button-4>", self._on_mouse_wheel)    # Linux scroll up
        widget.bind("<Button-5>", self._on_mouse_wheel)    # Linux scroll down

        for child in widget.winfo_children():
            self.bind_mouse_wheel(child)

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        # Button-5 or negative delta = scroll down
        if event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        # Button-4 or positive delta = scroll up
        elif event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")

    def scroll_to_top(self):
        """Scroll to the top of the content"""
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """Scroll to the bottom of the content"""
        self.canvas.yview_moveto(1)
