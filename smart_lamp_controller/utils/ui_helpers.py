#!/usr/bin/env python3
"""
UI Helpers - Common tkinter UI patterns and widgets
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, List, Tuple


def create_labeled_slider(
    parent: ttk.Frame,
    label_text: str,
    variable: tk.Variable,
    from_: float,
    to: float,
    command: Optional[Callable] = None,
    description: Optional[str] = None
) -> Tuple[ttk.Label, ttk.Scale]:
    """
    Create a labeled slider with optional description.
    Returns the label and scale widgets.
    """
    ttk.Label(parent, text=label_text).pack(anchor=tk.W)

    if description:
        ttk.Label(
            parent,
            text=description,
            font=("Segoe UI", 8),
            foreground="#666666"
        ).pack(anchor=tk.W)

    scale = ttk.Scale(
        parent,
        from_=from_,
        to=to,
        variable=variable,
        orient=tk.HORIZONTAL,
        command=command
    )
    scale.pack(fill=tk.X, pady=(5, 10))

    return scale


def create_button_group(
    parent: ttk.Frame,
    buttons: List[Tuple[str, Callable]],
    horizontal: bool = True,
    expand: bool = True
) -> List[ttk.Button]:
    """
    Create a group of buttons.
    buttons: List of (text, command) tuples
    Returns list of created button widgets.
    """
    frame = ttk.Frame(parent)
    frame.pack(fill=tk.X if horizontal else tk.Y, pady=5)

    created_buttons = []
    side = tk.LEFT if horizontal else tk.TOP

    for i, (text, command) in enumerate(buttons):
        btn = ttk.Button(frame, text=text, command=command)
        padx = (0, 5) if horizontal and i < len(buttons) - 1 else 0
        pady = (0, 5) if not horizontal and i < len(buttons) - 1 else 0

        if expand and horizontal:
            btn.pack(side=side, expand=True, fill=tk.X, padx=padx)
        else:
            btn.pack(side=side, padx=padx, pady=pady)

        created_buttons.append(btn)

    return created_buttons


def create_labeled_frame(
    parent: tk.Widget,
    title: str,
    padding: str = "10"
) -> ttk.LabelFrame:
    """Create and pack a labeled frame"""
    frame = ttk.LabelFrame(parent, text=title, padding=padding)
    frame.pack(fill=tk.X, pady=5)
    return frame


def create_color_swatch(
    parent: tk.Widget,
    color: str = "#ff0000",
    width: int = 30,
    height: int = 30,
    command: Optional[Callable] = None
) -> tk.Label:
    """Create a clickable color swatch"""
    swatch = tk.Label(
        parent,
        bg=color,
        width=width // 10,
        height=height // 20,
        relief="raised",
        bd=2
    )

    if command:
        swatch.bind("<Button-1>", lambda e: command())
        swatch.config(cursor="hand2")

    return swatch


def create_toggle_button(
    parent: tk.Widget,
    text_on: str,
    text_off: str,
    command: Callable,
    initial_state: bool = False
) -> ttk.Button:
    """
    Create a toggle button that switches text based on state.
    Returns the button. Use button.is_on to check state.
    """
    btn = ttk.Button(parent, text=text_off if not initial_state else text_on)
    btn.is_on = initial_state

    def toggle():
        btn.is_on = not btn.is_on
        btn.config(text=text_on if btn.is_on else text_off)
        command(btn.is_on)

    btn.config(command=toggle)
    return btn


def create_radio_group(
    parent: ttk.Frame,
    label_text: str,
    options: List[Tuple[str, str]],
    variable: tk.StringVar,
    command: Optional[Callable] = None
) -> List[ttk.Radiobutton]:
    """
    Create a group of radio buttons.
    options: List of (value, text) tuples
    Returns list of created radio buttons.
    """
    ttk.Label(parent, text=label_text).pack(anchor=tk.W, pady=(0, 5))

    radios = []
    for value, text in options:
        rb = ttk.Radiobutton(
            parent,
            text=text,
            variable=variable,
            value=value,
            command=command
        )
        rb.pack(anchor=tk.W, pady=2)
        radios.append(rb)

    return radios


def create_status_label(
    parent: tk.Widget,
    initial_text: str = "Ready"
) -> Tuple[tk.StringVar, ttk.Label]:
    """Create a status label with a StringVar for easy updates"""
    var = tk.StringVar(value=initial_text)
    label = ttk.Label(parent, textvariable=var, font=("Segoe UI", 9))
    return var, label


def show_tooltip(widget: tk.Widget, text: str, delay: int = 500):
    """Add a tooltip to a widget"""
    tooltip = None

    def show(event):
        nonlocal tooltip
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 5

        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            tooltip,
            text=text,
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padding=(5, 2)
        )
        label.pack()

    def hide(event):
        nonlocal tooltip
        if tooltip:
            tooltip.destroy()
            tooltip = None

    widget.bind("<Enter>", lambda e: widget.after(delay, lambda: show(e)))
    widget.bind("<Leave>", hide)
