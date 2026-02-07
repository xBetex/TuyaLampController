#!/usr/bin/env python3
"""
Base Tab - Common functionality for all tab components
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional
import sys
import os

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils.scrollable_frame import ScrollableFrame


class BaseTab:
    """
    Base class for tab components.
    Provides common setup and access to shared resources.
    """

    def __init__(self, notebook: ttk.Notebook, controller):
        """
        Initialize the tab.

        Args:
            notebook: The parent notebook widget
            controller: Reference to the main LampControllerUI for accessing
                        device_manager, effects_engine, config, etc.
        """
        self.notebook = notebook
        self.controller = controller
        self.frame: Optional[ttk.Frame] = None
        self.content: Optional[ttk.Frame] = None

        # Convenience references
        self.device_manager = controller.device_manager
        self.effects_engine = controller.effects_engine
        self.config = controller.config

    @property
    def root(self):
        """Get the root window"""
        return self.controller.root

    @property
    def status_var(self):
        """Get the status variable from controller"""
        return self.controller.status_var

    def setup(self):
        """
        Create and add the tab to the notebook.
        Subclasses should override _build_content() to add widgets.
        """
        self.frame = ttk.Frame(self.notebook)
        self.notebook.add(self.frame, text=self.get_tab_title())

        # Use ScrollableFrame for content
        scroll_wrapper = ScrollableFrame(self.frame)
        scroll_wrapper.pack(fill=tk.BOTH, expand=True)

        self.content = ttk.Frame(scroll_wrapper.scrollable_frame, padding="15")
        self.content.pack(fill=tk.BOTH, expand=True)

        # Build tab-specific content
        self._build_content()

        # Bind mouse wheel to scroll wrapper
        scroll_wrapper.bind_mouse_wheel(self.content)

    def get_tab_title(self) -> str:
        """Return the title for this tab. Override in subclass."""
        return "Tab"

    def _build_content(self):
        """Build the tab content. Override in subclass."""
        pass

    def create_labeled_frame(self, title: str, padding: str = "10") -> ttk.LabelFrame:
        """Create and pack a labeled frame"""
        frame = ttk.LabelFrame(self.content, text=title, padding=padding)
        frame.pack(fill=tk.X, pady=(0, 10))
        return frame

    def show_warning(self, title: str, message: str):
        """Show a warning message box"""
        from tkinter import messagebox
        messagebox.showwarning(title, message)

    def show_error(self, title: str, message: str):
        """Show an error message box"""
        from tkinter import messagebox
        messagebox.showerror(title, message)

    def check_connection(self) -> bool:
        """Check if device is connected, show warning if not"""
        if not self.device_manager.is_connected:
            self.show_warning("Connection", "Not connected to lamp!")
            return False
        return True
