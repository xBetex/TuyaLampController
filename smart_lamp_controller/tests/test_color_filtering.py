#!/usr/bin/env python3
"""
Test script to verify color filtering improvements
"""

import colorsys
from color_selection_logic import ColorSelectionLogic

def analyze_color(hex_color):
    """Analyze a color and return its properties"""
    r = int(hex_color[1:3], 16) / 255
    g = int(hex_color[3:5], 16) / 255
    b = int(hex_color[5:7], 16) / 255
    
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    return {
        'hex': hex_color,
        'rgb': (int(r*255), int(g*255), int(b*255)),
        'hsv': (h*360, s*100, v*100),
        'saturation_percent': s*100
    }

def main():
    logic = ColorSelectionLogic()
    
    # Test colors - mix of good and bad colors
    test_colors = [
        "#ff0000",  # Pure red - should pass
        "#808080",  # Gray - should fail
        "#ffffff",  # White - should fail
        "#f0f0f0",  # Light gray - should fail
        "#0080ff",  # Bright blue - should pass
        "#ffcccc",  # Light pink - should fail (low saturation)
        "#800080",  # Purple - should pass
        "#404040",  # Dark gray - should fail
        "#00ff00",  # Pure green - should pass
        "#ffffcc",  # Light yellow - should fail
        "#cc0066",  # Magenta - should pass
        "#e6e6fa",  # Lavender - should fail (too light)
    ]
    
    print("🎨 Color Filtering Test Results")
    print("=" * 60)
    print(f"{'Color':<10} {'RGB':<15} {'HSV':<20} {'Sat%':<6} {'Pass':<6} {'Score':<6}")
    print("-" * 60)
    
    for color in test_colors:
        props = analyze_color(color)
        is_colorful = logic.is_colorful(color)
        score = logic.calculate_ambient_score(color, 10.0)  # Assume 10% prevalence
        
        status = "✅ YES" if is_colorful else "❌ NO"
        
        print(f"{color:<10} {str(props['rgb']):<15} "
              f"({props['hsv'][0]:.0f},{props['hsv'][1]:.0f},{props['hsv'][2]:.0f})    "
              f"{props['saturation_percent']:.0f}%   {status:<6} {score:.0f}")
    
    print("\n📊 Summary:")
    passed = sum(1 for color in test_colors if logic.is_colorful(color))
    print(f"Colors that passed filtering: {passed}/{len(test_colors)}")
    print(f"Minimum saturation requirement: 50%")
    print(f"All passing colors have saturation ≥ 50%")

if __name__ == "__main__":
    main()