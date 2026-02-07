#!/usr/bin/env python3
"""
Color Selection Logic - Core logic for color mapping and justification
Separated logic that can be used by any UI component
"""

import colorsys
from typing import Tuple, Dict, List, Optional, Callable
try:
    import mss
    import numpy as np
    from PIL import Image, ImageTk
    SCREEN_CAPTURE_AVAILABLE = True
except ImportError:
    SCREEN_CAPTURE_AVAILABLE = False

# Import color decision types for score breakdowns
try:
    from color_decision import ColorScoreBreakdown, ColorCandidate, ColorDecisionReport
    COLOR_DECISION_AVAILABLE = True
except ImportError:
    COLOR_DECISION_AVAILABLE = False

class ColorSelectionLogic:
    """Core logic for color selection, analysis, and justification"""
    
    def __init__(self):
        self.selected_color = "#ff0000"
        self.selected_position = (0.5, 0.5)  # Normalized coordinates (0-1)
        self.monitor_index = 1  # Default to first monitor
        self.screen_thumbnail = None
        self.thumbnail_size = (160, 120)
    
    def capture_screen_thumbnail(self, monitor_index: int = None) -> Optional[any]:
        """Capture a thumbnail of the specified monitor"""
        if not SCREEN_CAPTURE_AVAILABLE:
            return None
            
        if monitor_index is None:
            monitor_index = self.monitor_index
            
        try:
            with mss.mss() as sct:
                if monitor_index >= len(sct.monitors):
                    monitor_index = 1
                    
                monitor = sct.monitors[monitor_index]
                
                # Capture screen
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Resize to thumbnail
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Store for later use
                self.screen_thumbnail = img
                
                return img
                
        except Exception as e:
            print(f"Screen capture error: {e}")
            return None
    
    def get_screen_thumbnail_tk(self) -> Optional[any]:
        """Get screen thumbnail as Tkinter PhotoImage"""
        if not SCREEN_CAPTURE_AVAILABLE or self.screen_thumbnail is None:
            return None
            
        try:
            return ImageTk.PhotoImage(self.screen_thumbnail)
        except Exception:
            return None
    
    def get_color_at_screen_position(self, position: Tuple[float, float], monitor_index: int = None) -> Optional[str]:
        """Get the actual color at the specified screen position"""
        if not SCREEN_CAPTURE_AVAILABLE:
            return None
            
        if monitor_index is None:
            monitor_index = self.monitor_index
            
        try:
            with mss.mss() as sct:
                if monitor_index >= len(sct.monitors):
                    monitor_index = 1
                    
                monitor = sct.monitors[monitor_index]
                
                # Calculate actual pixel position
                x = int(monitor['left'] + position[0] * monitor['width'])
                y = int(monitor['top'] + position[1] * monitor['height'])
                
                # Capture small area around the point
                region = {
                    'left': max(monitor['left'], x - 5),
                    'top': max(monitor['top'], y - 5),
                    'width': 10,
                    'height': 10
                }
                
                screenshot = sct.grab(region)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Get average color from the small region
                pixels = list(img.getdata())
                if pixels:
                    avg_r = sum(p[0] for p in pixels) // len(pixels)
                    avg_g = sum(p[1] for p in pixels) // len(pixels)
                    avg_b = sum(p[2] for p in pixels) // len(pixels)
                    
                    return '#{:02x}{:02x}{:02x}'.format(avg_r, avg_g, avg_b)
                    
        except Exception as e:
            print(f"Color sampling error: {e}")
            
        return None
    
    def analyze_color_prevalence(self, target_color: str, tolerance: float = 0.15) -> Optional[any]:
        """Analyze how prevalent a color is in the current screen thumbnail"""
        if not SCREEN_CAPTURE_AVAILABLE or self.screen_thumbnail is None:
            return None
            
        try:
            import numpy as np
            
            # Convert target color to RGB
            target_r = int(target_color[1:3], 16)
            target_g = int(target_color[3:5], 16) 
            target_b = int(target_color[5:7], 16)
            
            # Convert PIL image to numpy array
            img_array = np.array(self.screen_thumbnail)
            
            # Calculate color distance for each pixel
            r_diff = (img_array[:, :, 0] - target_r) / 255.0
            g_diff = (img_array[:, :, 1] - target_g) / 255.0
            b_diff = (img_array[:, :, 2] - target_b) / 255.0
            
            # Euclidean distance in RGB space
            color_distance = np.sqrt(r_diff**2 + g_diff**2 + b_diff**2)
            
            # Create mask for similar colors
            similar_mask = color_distance <= tolerance
            
            # Create highlighted image
            highlighted = img_array.copy()
            
            # Dim non-matching pixels
            highlighted[~similar_mask] = highlighted[~similar_mask] * 0.3
            
            # Enhance matching pixels
            highlighted[similar_mask] = np.minimum(highlighted[similar_mask] * 1.5, 255)
            
            # Add bright overlay to matching pixels
            overlay_color = np.array([target_r, target_g, target_b])
            highlighted[similar_mask] = np.minimum(
                highlighted[similar_mask] * 0.7 + overlay_color * 0.3, 255
            )
            
            # Convert back to PIL Image
            result_img = Image.fromarray(highlighted.astype(np.uint8))
            
            # Calculate prevalence percentage
            total_pixels = similar_mask.size
            matching_pixels = np.sum(similar_mask)
            prevalence = (matching_pixels / total_pixels) * 100
            
            return {
                'highlighted_image': result_img,
                'prevalence_percent': prevalence,
                'matching_pixels': matching_pixels,
                'total_pixels': total_pixels
            }
            
        except Exception as e:
            print(f"Color prevalence analysis error: {e}")
            return None
    
    def get_dominant_colors(self, num_colors: int = 5) -> List[Tuple[str, float]]:
        """Get the most dominant colors from the screen thumbnail - filtered to exclude grays/blacks"""
        if not SCREEN_CAPTURE_AVAILABLE or self.screen_thumbnail is None:
            return []
            
        try:
            import numpy as np
            from collections import Counter
            
            # Convert to numpy array and reshape to list of pixels
            img_array = np.array(self.screen_thumbnail)
            pixels = img_array.reshape(-1, 3)
            
            # Quantize colors to reduce noise (group similar colors)
            quantized = (pixels // 32) * 32  # Reduce to 8 levels per channel
            
            # Count color frequencies
            unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)
            
            # Sort by frequency
            sorted_indices = np.argsort(counts)[::-1]
            
            # Get colors and filter out grays/blacks/whites
            filtered_colors = []
            total_pixels = len(pixels)
            
            for i in range(len(unique_colors)):
                idx = sorted_indices[i]
                color_rgb = unique_colors[idx]
                frequency = counts[idx]
                percentage = (frequency / total_pixels) * 100
                
                # Convert to hex
                hex_color = '#{:02x}{:02x}{:02x}'.format(
                    int(color_rgb[0]), int(color_rgb[1]), int(color_rgb[2])
                )
                
                # Filter out grays, blacks, and whites
                if self.is_colorful(hex_color):
                    filtered_colors.append((hex_color, percentage))
                
                # Stop when we have enough colorful colors
                if len(filtered_colors) >= num_colors:
                    break
            
            return filtered_colors
            
        except Exception as e:
            print(f"Dominant color analysis error: {e}")
            return []
    
    def is_colorful(self, hex_color: str) -> bool:
        """Check if a color is actually colorful (not gray/black/white)"""
        try:
            # Convert to RGB
            r = int(hex_color[1:3], 16) / 255
            g = int(hex_color[3:5], 16) / 255
            b = int(hex_color[5:7], 16) / 255
            
            # Convert to HSV
            import colorsys
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            
            # STRICT Filter criteria:
            # 1. MUST have high saturation (vivid colors only) - MINIMUM 50%
            if s < 0.5:
                return False
            
            # 2. Must not be too dark (not black)
            if v < 0.2:
                return False
            
            # 3. AGGRESSIVE white filtering - reject anything too bright
            if v > 0.85:
                return False
            
            # 4. Additional white/cream filtering - check RGB variance
            rgb_avg = (r + g + b) / 3
            rgb_variance = ((r - rgb_avg)**2 + (g - rgb_avg)**2 + (b - rgb_avg)**2) / 3
            if rgb_variance < 0.02 and rgb_avg > 0.6:  # Low variance + bright = whitish
                return False
            
            # 5. Check if it's a skin tone (avoid)
            if self.is_skin_tone(r, g, b):
                return False
            
            # 6. Additional desaturated color check (catch pale colors)
            if s < 0.6 and v > 0.7:  # Pale/pastel colors
                return False
            
            return True
            
        except Exception:
            return False
    
    def coordinates_to_color(self, x: int, y: int, width: int, height: int) -> str:
        """Convert canvas coordinates to HSV color"""
        # Clamp coordinates
        x = max(0, min(width - 1, x))
        y = max(0, min(height - 1, y))
        
        # Calculate HSV from position
        hue = x / width
        saturation = 1.0 - (y / height * 0.3)  # High saturation, slight variation
        value = 1.0 - (y / height * 0.5)  # Brightness varies with height
        
        # Convert to RGB and hex
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))
    
    def color_to_coordinates(self, hex_color: str, width: int, height: int) -> Tuple[int, int]:
        """Convert hex color to approximate canvas coordinates"""
        r, g, b = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        x = int(h * width)
        y = int((1 - v * 0.5) * height)
        
        return (x, y)
    
    def analyze_color_properties(self, hex_color: str) -> Dict[str, float]:
        """Analyze color properties and return HSV values"""
        r = int(hex_color[1:3], 16) / 255
        g = int(hex_color[3:5], 16) / 255
        b = int(hex_color[5:7], 16) / 255
        
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        
        return {
            'hue': h,
            'saturation': s,
            'value': v,
            'hue_degrees': h * 360,
            'rgb': (int(r*255), int(g*255), int(b*255))
        }
    
    def generate_color_justification(self, hex_color: str, position: Tuple[float, float]) -> str:
        """Generate intelligent justification for color choice"""
        props = self.analyze_color_properties(hex_color)
        justifications = []
        
        # Hue-based justification
        hue_deg = props['hue_degrees']
        if 0 <= hue_deg < 30 or 330 <= hue_deg < 360:
            justifications.append("Red tones provide energy and attention-grabbing presence")
        elif 30 <= hue_deg < 90:
            justifications.append("Warm yellow-orange creates welcoming, cozy atmosphere")
        elif 90 <= hue_deg < 150:
            justifications.append("Green hues offer calming, natural ambiance")
        elif 150 <= hue_deg < 210:
            justifications.append("Cool cyan-blue promotes focus and tranquility")
        elif 210 <= hue_deg < 270:
            justifications.append("Blue tones enhance concentration and relaxation")
        elif 270 <= hue_deg < 330:
            justifications.append("Purple-magenta adds creative, luxurious feel")
        
        # Saturation-based justification
        s = props['saturation']
        if s > 0.8:
            justifications.append("High saturation ensures vivid, impactful lighting")
        elif s > 0.5:
            justifications.append("Moderate saturation balances vibrancy with subtlety")
        else:
            justifications.append("Low saturation provides gentle, ambient lighting")
        
        # Value/brightness-based justification
        v = props['value']
        if v > 0.8:
            justifications.append("Bright intensity maximizes visibility and presence")
        elif v > 0.5:
            justifications.append("Medium brightness offers comfortable illumination")
        else:
            justifications.append("Dim setting creates subtle mood lighting")
        
        # Position-based justification
        pos_x, pos_y = position
        if pos_x < 0.3:
            justifications.append("Left positioning draws attention to workspace area")
        elif pos_x > 0.7:
            justifications.append("Right positioning complements entertainment zone")
        else:
            justifications.append("Center positioning provides balanced room illumination")
        
        # Combine justifications (limit to 2 main points)
        return ". ".join(justifications[:2]) + "."
    
    def get_color_category(self, hex_color: str) -> str:
        """Get color category name"""
        props = self.analyze_color_properties(hex_color)
        hue_deg = props['hue_degrees']
        
        if 0 <= hue_deg < 30 or 330 <= hue_deg < 360:
            return "Red"
        elif 30 <= hue_deg < 90:
            return "Orange/Yellow"
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
    
    def blend_color_with_alpha(self, hex_color: str, alpha: float) -> str:
        """Simulate alpha blending with black background"""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Blend with black background
        r = int(r * alpha)
        g = int(g * alpha)
        b = int(b * alpha)
        
        return '#{:02x}{:02x}{:02x}'.format(r, g, b)
    
    def get_preset_colors(self) -> List[Tuple[str, str]]:
        """Get list of preset colors with names"""
        return [
            ("#ff0000", "Energetic Red"),
            ("#ff8000", "Warm Orange"),
            ("#ffff00", "Cheerful Yellow"),
            ("#00ff00", "Calming Green"),
            ("#0080ff", "Focus Blue"),
            ("#8000ff", "Creative Purple"),
            ("#ff0080", "Vibrant Pink"),
            ("#00ffff", "Cool Cyan")
        ]
    
    def get_preset_positions(self) -> List[Tuple[Tuple[float, float], str]]:
        """Get list of preset positions with names"""
        return [
            ((0.2, 0.2), "Top Left"),
            ((0.5, 0.2), "Top Center"),
            ((0.8, 0.2), "Top Right"),
            ((0.2, 0.5), "Center Left"),
            ((0.5, 0.5), "Center"),
            ((0.8, 0.5), "Center Right"),
            ((0.2, 0.8), "Bottom Left"),
            ((0.5, 0.8), "Bottom Center"),
            ((0.8, 0.8), "Bottom Right")
        ]
    
    def update_selection(self, color: str, position: Tuple[float, float]):
        """Update current selection"""
        self.selected_color = color
        self.selected_position = position
    
    def get_selection_info(self) -> Dict:
        """Get current selection information"""
        props = self.analyze_color_properties(self.selected_color)
        justification = self.generate_color_justification(self.selected_color, self.selected_position)
        category = self.get_color_category(self.selected_color)
        
        return {
            'color': self.selected_color,
            'position': self.selected_position,
            'position_percent': (int(self.selected_position[0] * 100), int(self.selected_position[1] * 100)),
            'properties': props,
            'justification': justification,
            'category': category
        }
    
    def get_best_ambient_color(self, dominant_colors) -> Optional[str]:
        """Automatically select the best color for ambient lighting"""
        if not dominant_colors:
            return None
        
        best_color = None
        best_score = -1
        
        for color, percentage in dominant_colors:
            score = self.calculate_ambient_score(color, percentage)
            if score > best_score:
                best_score = score
                best_color = color
        
        return best_color if best_score > 0 else None
    
    def calculate_ambient_score(self, hex_color: str, percentage: float) -> float:
        """Calculate how good a color is for ambient lighting"""
        try:
            # Convert to RGB
            r = int(hex_color[1:3], 16) / 255
            g = int(hex_color[3:5], 16) / 255
            b = int(hex_color[5:7], 16) / 255
            
            # Convert to HSV for analysis
            import colorsys
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            
            score = 0
            
            # 1. STRICT Saturation requirement (MINIMUM 50%)
            if s >= 0.5:  # Must have at least 50% saturation
                score += s * 60  # Up to 60 points for high saturation
                if s >= 0.7:  # Bonus for very saturated colors
                    score += 20
            else:
                return 0  # Immediately reject low saturation colors
            
            # 2. Brightness bonus (not too dark, not too bright)
            if 0.25 < v < 0.8:  # Tighter brightness range, avoid whites
                score += 30
            elif v < 0.15:  # Too dark (black)
                score -= 50
            elif v > 0.85:  # Too bright (white) - heavy penalty
                score -= 50
            
            # 3. Percentage bonus (more prevalent = better)
            if percentage > 3:  # At least 3% of screen
                score += min(percentage * 2.5, 25)  # Up to 25 points
            
            # 4. Color preference (vivid colors work better for ambient)
            hue_deg = h * 360
            if 200 <= hue_deg <= 280:  # Blues/purples - great for ambient
                score += 20
            elif 280 <= hue_deg <= 340:  # Purples/magentas - great
                score += 18
            elif 0 <= hue_deg <= 60 or 300 <= hue_deg <= 360:  # Reds - good
                score += 15
            elif 120 <= hue_deg <= 180:  # Greens - decent
                score += 10
            elif 60 <= hue_deg <= 120:  # Yellows/oranges - okay if saturated
                score += 8
            
            # 5. AGGRESSIVE penalties for unwanted colors
            if self.is_skin_tone(r, g, b):
                score -= 40  # Heavy penalty for skin tones
            
            if self.is_too_similar_to_white_light(r, g, b):
                score -= 30  # Heavy penalty for white-like colors
            
            # 6. Additional penalty for desaturated colors that slipped through
            if s < 0.6:
                score -= 15
            
            # 7. Bonus for highly saturated, vivid colors
            if s > 0.8 and 0.3 < v < 0.7:
                score += 15  # Bonus for perfect vivid colors
            
            return max(0, score)  # Don't return negative scores

        except Exception:
            return 0

    def calculate_ambient_score_with_breakdown(self, hex_color: str, percentage: float) -> "ColorScoreBreakdown":
        """Calculate score with detailed breakdown for transparency"""
        if not COLOR_DECISION_AVAILABLE:
            # Fallback if data classes not available
            return None

        breakdown = ColorScoreBreakdown()

        try:
            # Convert to RGB
            r = int(hex_color[1:3], 16) / 255
            g = int(hex_color[3:5], 16) / 255
            b = int(hex_color[5:7], 16) / 255

            # Convert to HSV
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            hue_deg = h * 360

            # 1. Saturation scoring (minimum 50%)
            if s >= 0.5:
                breakdown.saturation_score = s * 60
                if s >= 0.7:
                    breakdown.saturation_score += 20
                    breakdown.saturation_reason = f"Excellent saturation ({s*100:.0f}%) - vivid color"
                else:
                    breakdown.saturation_reason = f"Good saturation ({s*100:.0f}%) - acceptable vibrancy"
            else:
                breakdown.saturation_score = 0
                breakdown.saturation_reason = f"REJECTED: Low saturation ({s*100:.0f}%) - too washed out"
                # Early return for rejected colors
                return breakdown

            # 2. Brightness scoring
            if 0.25 < v < 0.8:
                breakdown.brightness_score = 30
                breakdown.brightness_reason = f"Ideal brightness ({v*100:.0f}%) - comfortable for ambient"
            elif v < 0.15:
                breakdown.brightness_score = -50
                breakdown.brightness_reason = f"Too dark ({v*100:.0f}%) - would be nearly invisible"
            elif v > 0.85:
                breakdown.brightness_score = -50
                breakdown.brightness_reason = f"Too bright ({v*100:.0f}%) - approaches white light"
            elif v <= 0.25:
                breakdown.brightness_score = 0
                breakdown.brightness_reason = f"Marginally dark ({v*100:.0f}%)"
            else:  # 0.8 <= v <= 0.85
                breakdown.brightness_score = 0
                breakdown.brightness_reason = f"Marginally bright ({v*100:.0f}%)"

            # 3. Prevalence scoring
            if percentage > 3:
                breakdown.prevalence_score = min(percentage * 2.5, 25)
                breakdown.prevalence_reason = f"Covers {percentage:.1f}% of screen - significant presence"
            else:
                breakdown.prevalence_score = 0
                breakdown.prevalence_reason = f"Only {percentage:.1f}% of screen - minor presence"

            # 4. Hue preference scoring
            hue_prefs = [
                ((200, 280), "Blue/Purple", 20, "ideal for relaxation and focus"),
                ((280, 340), "Magenta/Pink", 18, "creative and energetic"),
                ((0, 60), "Red/Orange", 15, "warm and attention-grabbing"),
                ((300, 360), "Red", 15, "warm and attention-grabbing"),
                ((120, 180), "Green/Cyan", 10, "calming but less impactful"),
                ((60, 120), "Yellow/Green", 8, "visible but less ambient"),
            ]

            breakdown.hue_preference_score = 8  # Default
            breakdown.hue_reason = f"Neutral hue ({hue_deg:.0f}°)"

            for (h_min, h_max), name, score, reason in hue_prefs:
                if h_min <= hue_deg < h_max:
                    breakdown.hue_preference_score = score
                    breakdown.hue_reason = f"{name} hue ({hue_deg:.0f}°) - {reason}"
                    break

            # 5. Penalties
            breakdown.penalty_reasons = []

            if self.is_skin_tone(r, g, b):
                breakdown.penalties -= 40
                breakdown.penalty_reasons.append("Skin tone detected (-40)")

            if self.is_too_similar_to_white_light(r, g, b):
                breakdown.penalties -= 30
                breakdown.penalty_reasons.append("Too close to white light (-30)")

            if s < 0.6:
                breakdown.penalties -= 15
                breakdown.penalty_reasons.append("Borderline saturation (-15)")

            # Bonus for highly saturated, vivid colors
            if s > 0.8 and 0.3 < v < 0.7:
                breakdown.penalties += 15  # Using penalties field for bonus too
                breakdown.penalty_reasons.append("Vivid color bonus (+15)")

            return breakdown

        except Exception as e:
            breakdown.saturation_reason = f"Error analyzing color: {e}"
            return breakdown

    def get_best_ambient_color_with_report(self, dominant_colors) -> Tuple[Optional[str], Optional["ColorDecisionReport"]]:
        """Select the best color and return a detailed decision report"""
        if not COLOR_DECISION_AVAILABLE or not dominant_colors:
            # Fallback to simple method
            return self.get_best_ambient_color(dominant_colors), None

        candidates = []
        best_color = None
        best_score = -1
        best_candidate = None

        for color, percentage in dominant_colors:
            # Get breakdown
            breakdown = self.calculate_ambient_score_with_breakdown(color, percentage)

            if breakdown is None:
                continue

            # Convert to RGB and HSV for candidate
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

            # Determine if rejected
            rejection_reason = None
            if breakdown.total_score == 0:
                if "REJECTED" in breakdown.saturation_reason:
                    rejection_reason = breakdown.saturation_reason
                elif breakdown.brightness_score <= -50:
                    rejection_reason = breakdown.brightness_reason

            candidate = ColorCandidate(
                hex_color=color,
                rgb=(r, g, b),
                hsv=(h, s, v),
                screen_percentage=percentage,
                score_breakdown=breakdown,
                is_winner=False,
                rejection_reason=rejection_reason
            )
            candidates.append(candidate)

            # Track best
            if breakdown.total_score > best_score:
                best_score = breakdown.total_score
                best_color = color
                best_candidate = candidate

        # Mark winner
        if best_candidate and best_score > 0:
            best_candidate.is_winner = True
        else:
            best_candidate = None

        # Create report
        report = ColorDecisionReport.create(
            winner=best_candidate,
            candidates=candidates,
            screen_thumbnail=self.screen_thumbnail
        )

        return best_color if best_score > 0 else None, report

    def is_skin_tone(self, r: float, g: float, b: float) -> bool:
        """Check if color is likely a skin tone"""
        # Simple skin tone detection
        return (r > 0.6 and g > 0.4 and b > 0.2 and 
                r > g > b and 
                (r - b) > 0.2)
    
    def is_too_similar_to_white_light(self, r: float, g: float, b: float) -> bool:
        """Check if color is too similar to white/warm white light"""
        # More aggressive white detection
        avg = (r + g + b) / 3
        variance = ((r - avg)**2 + (g - avg)**2 + (b - avg)**2) / 3
        
        # Reject if:
        # 1. Low variance + bright = white-ish
        if variance < 0.015 and avg > 0.5:
            return True
        
        # 2. Very bright overall (catches near-whites)
        if avg > 0.8:
            return True
        
        # 3. All channels high (RGB white detection)
        if r > 0.75 and g > 0.75 and b > 0.75:
            return True
        
        return False