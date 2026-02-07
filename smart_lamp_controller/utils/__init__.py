"""
Utils package - Shared utilities for Smart Lamp Controller
"""

from .color_utils import (
    hex_to_rgb,
    rgb_to_hex,
    hex_to_hsv,
    hsv_to_hex,
    apply_brightness,
    blend_colors,
    color_distance,
    get_hue_name,
    is_colorful,
    is_skin_tone,
    is_too_similar_to_white,
)

from .scrollable_frame import ScrollableFrame

from .ui_helpers import (
    create_labeled_slider,
    create_button_group,
    create_labeled_frame,
    create_color_swatch,
    create_toggle_button,
    create_radio_group,
    create_status_label,
    show_tooltip,
)

__all__ = [
    # Color utilities
    'hex_to_rgb',
    'rgb_to_hex',
    'hex_to_hsv',
    'hsv_to_hex',
    'apply_brightness',
    'blend_colors',
    'color_distance',
    'get_hue_name',
    'is_colorful',
    'is_skin_tone',
    'is_too_similar_to_white',
    # Scrollable frame
    'ScrollableFrame',
    # UI helpers
    'create_labeled_slider',
    'create_button_group',
    'create_labeled_frame',
    'create_color_swatch',
    'create_toggle_button',
    'create_radio_group',
    'create_status_label',
    'show_tooltip',
]
