#!/usr/bin/env python3
"""
Color Utilities - Shared color conversion and manipulation functions
"""

import colorsys
from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple (0-255)"""
    hex_color = hex_color.lstrip('#')
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values (0-255) to hex color string"""
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b)))
    )


def hex_to_hsv(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to HSV (0-1 range for all components)"""
    r, g, b = hex_to_rgb(hex_color)
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def hsv_to_hex(h: float, s: float, v: float) -> str:
    """Convert HSV (0-1 range) to hex color string"""
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))


def apply_brightness(hex_color: str, brightness: float) -> str:
    """Apply brightness multiplier (0-1) to a hex color"""
    r, g, b = hex_to_rgb(hex_color)
    brightness = max(0.0, min(1.0, brightness))
    return rgb_to_hex(
        int(r * brightness),
        int(g * brightness),
        int(b * brightness)
    )


def blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """Blend two hex colors. ratio=0 gives color1, ratio=1 gives color2"""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)
    ratio = max(0.0, min(1.0, ratio))

    return rgb_to_hex(
        int(r1 * (1 - ratio) + r2 * ratio),
        int(g1 * (1 - ratio) + g2 * ratio),
        int(b1 * (1 - ratio) + b2 * ratio)
    )


def color_distance(color1: str, color2: str) -> float:
    """Calculate Euclidean distance between two colors in RGB space (0-1 range)"""
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)

    return (
        ((r1 - r2) / 255) ** 2 +
        ((g1 - g2) / 255) ** 2 +
        ((b1 - b2) / 255) ** 2
    ) ** 0.5


def get_hue_name(hex_color: str) -> str:
    """Get human-readable name for the color's hue"""
    h, s, v = hex_to_hsv(hex_color)
    hue_deg = h * 360

    if s < 0.1:
        if v > 0.9:
            return "White"
        elif v < 0.1:
            return "Black"
        else:
            return "Gray"

    if 0 <= hue_deg < 30 or 330 <= hue_deg <= 360:
        return "Red"
    elif 30 <= hue_deg < 60:
        return "Orange"
    elif 60 <= hue_deg < 90:
        return "Yellow"
    elif 90 <= hue_deg < 150:
        return "Green"
    elif 150 <= hue_deg < 210:
        return "Cyan"
    elif 210 <= hue_deg < 270:
        return "Blue"
    elif 270 <= hue_deg < 330:
        return "Purple/Magenta"
    else:
        return "Unknown"


def is_colorful(hex_color: str, min_saturation: float = 0.5,
                min_value: float = 0.2, max_value: float = 0.85) -> bool:
    """Check if a color is actually colorful (not gray/black/white)"""
    h, s, v = hex_to_hsv(hex_color)

    if s < min_saturation:
        return False
    if v < min_value or v > max_value:
        return False

    return True


def is_skin_tone(r: float, g: float, b: float) -> bool:
    """Check if normalized RGB values (0-1) represent a skin tone"""
    return (r > 0.6 and g > 0.4 and b > 0.2 and
            r > g > b and
            (r - b) > 0.2)


def is_too_similar_to_white(r: float, g: float, b: float) -> bool:
    """Check if normalized RGB values are too similar to white light"""
    avg = (r + g + b) / 3
    variance = ((r - avg)**2 + (g - avg)**2 + (b - avg)**2) / 3

    # Low variance + bright = white-ish
    if variance < 0.015 and avg > 0.5:
        return True

    # Very bright overall
    if avg > 0.8:
        return True

    # All channels high
    if r > 0.75 and g > 0.75 and b > 0.75:
        return True

    return False
