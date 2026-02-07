#!/usr/bin/env python3
"""
Screen Color Analyzer - Ambilight Tuning & Screen Color Analysis Tool

Standalone application for real-time screen color analysis, ambilight parameter
tuning, and color extraction visualization. Provides live preview with crop overlay,
dominant color detection with proportions, 5-second color history timeline,
HSV color map, detailed color scoring, and live lamp simulation.
"""

import os
import sys
import time
import math
import colorsys
import threading
import logging
from collections import deque
from typing import List, Tuple, Optional, Dict

import tkinter as tk
from tkinter import ttk

# Optional dependencies
try:
    import mss
    import numpy as np
    from PIL import Image, ImageTk, ImageDraw
    CAPTURE_AVAILABLE = True
except ImportError:
    CAPTURE_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# Lamp control dependencies
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
for _sub in ("core", "utils", "src"):
    sys.path.insert(0, os.path.join(_BASE_DIR, _sub))

try:
    from config import Config
    from device_manager import DeviceManager
    LAMP_AVAILABLE = True
except ImportError:
    LAMP_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Color Utilities
# ═══════════════════════════════════════════════════════════════════════════════

def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        int(max(0, min(255, r))),
        int(max(0, min(255, g))),
        int(max(0, min(255, b))),
    )


def hex_to_hsv(hex_color: str) -> Tuple[float, float, float]:
    r, g, b = hex_to_rgb(hex_color)
    return colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)


def luminance(r: int, g: int, b: int) -> float:
    return 0.2126 * r / 255 + 0.7152 * g / 255 + 0.0722 * b / 255


def get_hue_name(h_deg: float) -> str:
    if h_deg < 15 or h_deg >= 345:
        return "Red"
    if h_deg < 45:
        return "Orange"
    if h_deg < 75:
        return "Yellow"
    if h_deg < 150:
        return "Green"
    if h_deg < 195:
        return "Cyan"
    if h_deg < 255:
        return "Blue"
    if h_deg < 285:
        return "Purple"
    if h_deg < 345:
        return "Magenta"
    return "Red"


def is_colorful(r, g, b, min_sat=0.5, min_val=0.2, max_val=0.85):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if s < min_sat or v < min_val or v > max_val:
        return False
    avg = (r + g + b) / (3 * 255)
    var = ((r / 255 - avg) ** 2 + (g / 255 - avg) ** 2 + (b / 255 - avg) ** 2) / 3
    if var < 0.02 and avg > 0.6:
        return False
    return True


def is_skin_tone(r, g, b):
    rf, gf, bf = r / 255, g / 255, b / 255
    return rf > 0.6 and gf > 0.4 and bf > 0.2 and rf > gf > bf and (rf - bf) > 0.2


# ═══════════════════════════════════════════════════════════════════════════════
# Color Scoring (mirrors color_selection_logic.py algorithm)
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_score_breakdown(hex_color: str, percentage: float) -> Dict:
    """Calculate ambient score with full breakdown for a color."""
    r, g, b = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h_deg = h * 360

    result = {
        "hex": hex_color,
        "rgb": (r, g, b),
        "hsv": (h, s, v),
        "h_deg": h_deg,
        "percentage": percentage,
        "category": get_hue_name(h_deg),
    }

    # Saturation score (0-80)
    if s < 0.5:
        result.update(sat_score=0, sat_reason=f"Rejected: {s * 100:.0f}% < 50% min",
                      bri_score=0, bri_reason="", prev_score=0, prev_reason="",
                      hue_score=0, hue_reason="", penalties=0, penalty_reasons=[],
                      total=0, rejected=True)
        return result

    sat_score = s * 60
    if s >= 0.7:
        sat_score += 20
    result["sat_score"] = round(sat_score, 1)
    result["sat_reason"] = f"{s * 100:.0f}% sat" + (" +vivid" if s >= 0.7 else "")

    # Brightness score (-50 to +30)
    if 0.25 < v < 0.8:
        bri_score = 30
        bri_reason = "Ideal range"
    elif v < 0.15:
        bri_score = -50
        bri_reason = f"Too dark ({v * 100:.0f}%)"
    elif v > 0.85:
        bri_score = -50
        bri_reason = f"Too bright ({v * 100:.0f}%)"
    else:
        bri_score = max(0, 30 - abs(v - 0.525) * 80)
        bri_reason = f"Edge range ({v * 100:.0f}%)"
    result["bri_score"] = round(bri_score, 1)
    result["bri_reason"] = bri_reason

    # Prevalence score (0-25)
    if percentage > 3:
        prev_score = min(percentage * 2.5, 25)
        prev_reason = f"{percentage:.1f}% of screen"
    else:
        prev_score = 0
        prev_reason = f"Too rare ({percentage:.1f}%)"
    result["prev_score"] = round(prev_score, 1)
    result["prev_reason"] = prev_reason

    # Hue preference (8-20)
    if 200 <= h_deg < 280:
        hue_score, hue_reason = 20, "Blue/Purple"
    elif 280 <= h_deg < 340:
        hue_score, hue_reason = 18, "Magenta/Pink"
    elif h_deg < 60 or h_deg >= 300:
        hue_score, hue_reason = 15, "Red tones"
    elif 120 <= h_deg < 180:
        hue_score, hue_reason = 10, "Green/Cyan"
    elif 60 <= h_deg < 120:
        hue_score, hue_reason = 8, "Yellow/Green"
    else:
        hue_score, hue_reason = 8, "Other"
    result["hue_score"] = hue_score
    result["hue_reason"] = hue_reason

    # Penalties / bonuses
    penalties = 0
    penalty_reasons = []
    if is_skin_tone(r, g, b):
        penalties -= 40
        penalty_reasons.append("Skin tone (-40)")
    if s < 0.6:
        penalties -= 15
        penalty_reasons.append("Low saturation (-15)")
    if s > 0.8 and 0.3 < v < 0.7:
        penalties += 15
        penalty_reasons.append("Vivid bonus (+15)")
    result["penalties"] = penalties
    result["penalty_reasons"] = penalty_reasons

    total = sat_score + bri_score + prev_score + hue_score + penalties
    result["total"] = round(max(0, total), 1)
    result["rejected"] = total <= 0
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# HSV Color Map Generator
# ═══════════════════════════════════════════════════════════════════════════════

def generate_colormap_array(width: int, height: int, value: float = 1.0) -> np.ndarray:
    """Generate an HSV color map as RGB numpy array. X=Hue, Y=Saturation."""
    h_vals = np.linspace(0, 1, width, endpoint=False)
    s_vals = np.linspace(1, 0, height)
    H, S = np.meshgrid(h_vals, s_vals)
    V = np.full_like(H, value)
    C = V * S
    H6 = H * 6.0
    X = C * (1 - np.abs(H6 % 2 - 1))
    m = V - C

    R, G, B = np.zeros_like(H), np.zeros_like(H), np.zeros_like(H)
    for i, (lo, hi) in enumerate([(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]):
        mask = (H6 >= lo) & (H6 < hi)
        if i == 0:
            R[mask], G[mask] = C[mask], X[mask]
        elif i == 1:
            R[mask], G[mask] = X[mask], C[mask]
        elif i == 2:
            G[mask], B[mask] = C[mask], X[mask]
        elif i == 3:
            G[mask], B[mask] = X[mask], C[mask]
        elif i == 4:
            R[mask], B[mask] = X[mask], C[mask]
        elif i == 5:
            R[mask], B[mask] = C[mask], X[mask]
    R += m
    G += m
    B += m
    rgb = np.stack([R, G, B], axis=-1)
    return (rgb * 255).clip(0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════════════════════════
# Screen Capture Engine
# ═══════════════════════════════════════════════════════════════════════════════

class ScreenCaptureEngine:
    """Background screen capture and color extraction engine."""

    def __init__(self):
        self.running = False
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None

        # Parameters
        self.monitor_index = 1
        self.crop_percent = 15
        self.alpha = 0.20
        self.mode = "accent"  # "average" or "accent"
        self.fps_limit = 12
        self.color_change_threshold = 0.03

        # Output state (read with lock)
        self.latest_frame: Optional[np.ndarray] = None  # Full RGB frame
        self.frame_size: Tuple[int, int] = (0, 0)  # (w, h)
        self.dominant_colors: List[Tuple[str, float]] = []  # Filtered (colorful)
        self.all_colors: List[Tuple[str, float]] = []  # Unfiltered top colors
        self.current_raw_hex: Optional[str] = None
        self.current_smooth_hex: Optional[str] = None
        self.would_send: bool = False
        self.color_history: deque = deque(maxlen=600)
        self.send_events: deque = deque(maxlen=300)
        self.fps_actual: float = 0.0
        self.new_data: bool = False
        self.pending_lamp_color: Optional[str] = None  # set on threshold exceed

        # Internal smoothing state
        self._smooth_rgb = None
        self._last_sent_rgb = None

    def get_monitors(self) -> List[str]:
        """Return list of monitor descriptions."""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                result = []
                for i, m in enumerate(monitors):
                    if i == 0:
                        result.append(f"0: All Monitors ({m['width']}x{m['height']})")
                    else:
                        result.append(f"{i}: Display {i} ({m['width']}x{m['height']})")
                return result
        except Exception as e:
            logger.error(f"Monitor detection error: {e}")
            return ["1: Default"]

    def start(self):
        if self.running:
            return
        self.running = True
        self._smooth_rgb = None
        self._last_sent_rgb = None
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.thread = None

    def _capture_loop(self):
        with mss.mss() as sct:
            while self.running:
                t0 = time.time()
                try:
                    monitors = sct.monitors
                    idx = min(self.monitor_index, len(monitors) - 1)
                    mon = monitors[idx]
                    raw = sct.grab(mon)

                    # Convert BGRA -> RGB numpy array
                    frame = np.array(raw)[:, :, :3][:, :, ::-1].copy()

                    # Process
                    self._process_frame(frame)

                except Exception as e:
                    logger.error(f"Capture error: {e}")
                    time.sleep(0.5)

                # FPS limiting
                elapsed = time.time() - t0
                target = 1.0 / max(self.fps_limit, 1)
                if elapsed < target:
                    time.sleep(target - elapsed)
                total = time.time() - t0
                self.fps_actual = 1.0 / max(total, 0.001)

    def _process_frame(self, frame: np.ndarray):
        h, w = frame.shape[:2]
        crop = self.crop_percent / 100.0
        my = int(h * crop)
        mx = int(w * crop)
        cropped = frame[my : h - my, mx : w - mx] if my > 0 or mx > 0 else frame

        if cropped.size == 0:
            return

        # Downscale for color analysis
        small = self._downscale(cropped, 64, 36)

        # Extract dominant colors (unfiltered + filtered)
        all_cols = self._extract_dominant(small, num=10, filter_colorful=False)
        dom_cols = self._extract_dominant(small, num=8, filter_colorful=True)

        # Extract output color
        raw_rgb = self._extract_output_color(small)
        raw_hex = rgb_to_hex(*raw_rgb)

        # Smoothing
        if self._smooth_rgb is None:
            self._smooth_rgb = np.array(raw_rgb, dtype=float)
        else:
            a = self.alpha * (0.7 if self.mode == "accent" else 1.0)
            self._smooth_rgb = a * np.array(raw_rgb) + (1 - a) * self._smooth_rgb
        sr, sg, sb = self._smooth_rgb.astype(int).clip(0, 255)
        smooth_hex = rgb_to_hex(int(sr), int(sg), int(sb))

        # Threshold check
        would_send = False
        if self._last_sent_rgb is not None:
            diff = np.sqrt(np.sum(((self._smooth_rgb - self._last_sent_rgb) / 255) ** 2))
            if diff > self.color_change_threshold:
                would_send = True
                self._last_sent_rgb = self._smooth_rgb.copy()
                self.send_events.append(time.time())
        else:
            self._last_sent_rgb = self._smooth_rgb.copy()
            would_send = True
            self.send_events.append(time.time())

        now = time.time()
        self.color_history.append((now, smooth_hex))

        with self.lock:
            self.latest_frame = frame
            self.frame_size = (w, h)
            self.all_colors = all_cols
            self.dominant_colors = dom_cols
            self.current_raw_hex = raw_hex
            self.current_smooth_hex = smooth_hex
            self.would_send = would_send
            if would_send:
                self.pending_lamp_color = smooth_hex
            self.new_data = True

    def _downscale(self, img: np.ndarray, tw: int, th: int) -> np.ndarray:
        if CV2_AVAILABLE:
            return cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        pil = Image.fromarray(img)
        pil = pil.resize((tw, th), Image.LANCZOS)
        return np.array(pil)

    def _extract_dominant(self, small: np.ndarray, num=8, filter_colorful=True) -> List[Tuple[str, float]]:
        pixels = small.reshape(-1, 3)
        quantized = (pixels // 32) * 32 + 16
        # Count unique
        uniq, counts = np.unique(quantized, axis=0, return_counts=True)
        total = counts.sum()
        order = counts.argsort()[::-1]
        uniq = uniq[order]
        counts = counts[order]

        result = []
        for i in range(len(uniq)):
            r, g, b = int(uniq[i][0]), int(uniq[i][1]), int(uniq[i][2])
            pct = float(counts[i]) / total * 100
            if filter_colorful and not is_colorful(r, g, b):
                continue
            result.append((rgb_to_hex(r, g, b), round(pct, 1)))
            if len(result) >= num:
                break
        return result

    def _pixels_to_hsv(self, pixels_flat: np.ndarray) -> np.ndarray:
        """Convert Nx3 RGB float pixels (0-255) to Nx3 HSV (0-1). Uses cv2 fast path if available."""
        if CV2_AVAILABLE:
            # cv2 expects uint8 BGR
            bgr = pixels_flat[:, ::-1].astype(np.uint8).reshape(1, -1, 3)
            hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(float)
            hsv[:, 0] /= 180.0  # H: 0-180 -> 0-1
            hsv[:, 1] /= 255.0  # S: 0-255 -> 0-1
            hsv[:, 2] /= 255.0  # V: 0-255 -> 0-1
            return hsv
        return np.array([colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                         for r, g, b in pixels_flat])

    def _extract_output_color(self, small: np.ndarray) -> Tuple[int, int, int]:
        """Extract the output color using average or accent mode."""
        pixels = small.reshape(-1, 3).astype(float)
        hsv_pixels = self._pixels_to_hsv(pixels)

        if self.mode == "average":
            # Filter dark/desaturated pixels
            mask = (hsv_pixels[:, 2] > 30 / 255) & (hsv_pixels[:, 1] > 20 / 255)
            if mask.sum() == 0:
                return (128, 128, 128)
            avg = pixels[mask].mean(axis=0)
            return (int(avg[0]), int(avg[1]), int(avg[2]))

        else:  # accent
            mask = (hsv_pixels[:, 2] > 40 / 255) & (hsv_pixels[:, 1] > 50 / 255)
            if mask.sum() == 0:
                # Fallback to less strict
                mask = (hsv_pixels[:, 2] > 30 / 255) & (hsv_pixels[:, 1] > 20 / 255)
            if mask.sum() == 0:
                return (128, 128, 128)

            # Hue histogram (18 bins)
            hues = hsv_pixels[mask, 0]
            hist, edges = np.histogram(hues, bins=18, range=(0, 1))
            dominant_bin = hist.argmax()
            bin_lo = edges[dominant_bin]
            bin_hi = edges[dominant_bin + 1]

            # Average pixels in dominant hue bin
            hue_mask = (hues >= bin_lo) & (hues < bin_hi)
            sat_vals = hsv_pixels[mask][hue_mask]
            rgb_vals = pixels[mask][hue_mask]

            if len(rgb_vals) == 0:
                avg = pixels[mask].mean(axis=0)
                return (int(avg[0]), int(avg[1]), int(avg[2]))

            # Boost saturation for accent
            dominance = hist[dominant_bin] / mask.sum()
            avg_rgb = rgb_vals.mean(axis=0)
            avg_h = sat_vals[:, 0].mean()
            avg_s = sat_vals[:, 1].mean()
            avg_v = sat_vals[:, 2].mean()

            if dominance > 0.3:
                target_s = 1.0
                target_v = max(0.78, avg_v)
            else:
                target_s = min(0.86, avg_s * 1.5)
                target_v = avg_v

            r, g, b = colorsys.hsv_to_rgb(avg_h, target_s, target_v)
            return (int(r * 255), int(g * 255), int(b * 255))


# ═══════════════════════════════════════════════════════════════════════════════
# GUI Application
# ═══════════════════════════════════════════════════════════════════════════════

CANVAS_BG = "#16161e"
PANEL_PAD = 6
PREVIEW_W, PREVIEW_H = 480, 270
COLORMAP_W, COLORMAP_H = 340, 170
HISTORY_H = 70
SIM_SIZE = 80


class ScreenColorAnalyzerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Screen Color Analyzer")
        self.root.geometry("1300x860")
        self.root.minsize(1000, 650)

        self.engine = ScreenCaptureEngine()
        self.selected_color: Optional[str] = None
        self._preview_photo = None  # prevent GC
        self._colormap_base_photo = None
        self._colormap_value = 0.85

        # Lamp connection state
        self.device_manager: Optional[object] = None
        self.lamp_connected = False
        self.lamp_send_enabled = False

        self._build_ui()
        self._populate_monitors()
        self._generate_colormap()
        self._draw_placeholder()
        self._update_loop()

    # ── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=5)
        self.root.columnconfigure(1, weight=4)
        self.root.columnconfigure(2, weight=4)
        self.root.rowconfigure(1, weight=1)

        self._build_toolbar()
        self._build_preview_panel()
        self._build_colors_panel()
        self._build_right_panel()
        self._build_history_panel()
        self._build_sim_panel()

    def _build_toolbar(self):
        tb = ttk.Frame(self.root)
        tb.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 2))

        # Monitor
        ttk.Label(tb, text="Monitor:").pack(side="left", padx=(0, 4))
        self.monitor_var = tk.StringVar()
        self.monitor_cb = ttk.Combobox(tb, textvariable=self.monitor_var,
                                       state="readonly", width=28)
        self.monitor_cb.pack(side="left", padx=(0, 14))
        self.monitor_cb.bind("<<ComboboxSelected>>", self._on_monitor_change)

        # Mode
        ttk.Label(tb, text="Mode:").pack(side="left", padx=(0, 4))
        self.mode_var = tk.StringVar(value="accent")
        mode_cb = ttk.Combobox(tb, textvariable=self.mode_var,
                               values=["average", "accent"], state="readonly", width=9)
        mode_cb.pack(side="left", padx=(0, 14))
        mode_cb.bind("<<ComboboxSelected>>", self._on_mode_change)

        # Start/Stop
        self.start_btn = ttk.Button(tb, text="\u25b6 Start", command=self._on_start_stop, width=10)
        self.start_btn.pack(side="left", padx=(0, 14))

        # Separator
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=(0, 14), pady=2)

        # Lamp controls
        self.connect_btn = ttk.Button(tb, text="\u26ab Connect Lamp",
                                      command=self._on_lamp_connect, width=15)
        self.connect_btn.pack(side="left", padx=(0, 6))
        if not LAMP_AVAILABLE:
            self.connect_btn.configure(state="disabled")

        self.send_var_toggle = tk.BooleanVar(value=False)
        self.send_check = ttk.Checkbutton(tb, text="Send to Lamp",
                                          variable=self.send_var_toggle,
                                          command=self._on_send_toggle)
        self.send_check.pack(side="left", padx=(0, 6))
        self.send_check.configure(state="disabled")

        self.lamp_status_var = tk.StringVar(value="")
        self.lamp_status_label = ttk.Label(tb, textvariable=self.lamp_status_var,
                                           font=("Consolas", 8))
        self.lamp_status_label.pack(side="left", padx=(0, 14))

        # FPS
        self.fps_var = tk.StringVar(value="FPS: --")
        ttk.Label(tb, textvariable=self.fps_var, width=12).pack(side="right")

        # Status indicator
        self.status_var = tk.StringVar(value="Stopped")
        ttk.Label(tb, textvariable=self.status_var, foreground="gray").pack(side="right", padx=(0, 14))

    def _build_preview_panel(self):
        frame = ttk.LabelFrame(self.root, text="Screen Preview")
        frame.grid(row=1, column=0, sticky="nsew", padx=(8, 3), pady=3)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        # Preview canvas
        self.preview_canvas = tk.Canvas(frame, bg=CANVAS_BG, width=PREVIEW_W,
                                        height=PREVIEW_H, highlightthickness=0)
        self.preview_canvas.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.preview_canvas.bind("<Button-1>", self._on_preview_click)
        self.preview_canvas.bind("<Motion>", self._on_preview_motion)
        self._preview_hex_var = tk.StringVar(value="")
        self._cursor_label = ttk.Label(frame, textvariable=self._preview_hex_var,
                                       font=("Consolas", 9))
        self._cursor_label.grid(row=1, column=0, sticky="w", padx=8)

        # Sliders
        ctrl = ttk.Frame(frame)
        ctrl.grid(row=2, column=0, sticky="ew", padx=4, pady=(2, 6))
        ctrl.columnconfigure(1, weight=1)

        ttk.Label(ctrl, text="Crop %:").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.crop_var = tk.IntVar(value=15)
        self.crop_slider = ttk.Scale(ctrl, from_=0, to=40, variable=self.crop_var,
                                     command=self._on_crop_change)
        self.crop_slider.grid(row=0, column=1, sticky="ew")
        self.crop_label = ttk.Label(ctrl, text="15%", width=5)
        self.crop_label.grid(row=0, column=2, padx=(4, 0))

        ttk.Label(ctrl, text="Smoothing:").grid(row=1, column=0, sticky="w", padx=(0, 4))
        self.alpha_var = tk.DoubleVar(value=0.20)
        self.alpha_slider = ttk.Scale(ctrl, from_=0.05, to=0.60, variable=self.alpha_var,
                                      command=self._on_alpha_change)
        self.alpha_slider.grid(row=1, column=1, sticky="ew")
        self.alpha_label = ttk.Label(ctrl, text="0.20", width=5)
        self.alpha_label.grid(row=1, column=2, padx=(4, 0))

        ttk.Label(ctrl, text="Threshold:").grid(row=2, column=0, sticky="w", padx=(0, 4))
        self.thresh_var = tk.DoubleVar(value=0.03)
        self.thresh_slider = ttk.Scale(ctrl, from_=0.01, to=0.15, variable=self.thresh_var,
                                       command=self._on_thresh_change)
        self.thresh_slider.grid(row=2, column=1, sticky="ew")
        self.thresh_label = ttk.Label(ctrl, text="3%", width=5)
        self.thresh_label.grid(row=2, column=2, padx=(4, 0))

        ttk.Label(ctrl, text="FPS Limit:").grid(row=3, column=0, sticky="w", padx=(0, 4))
        self.fpslim_var = tk.IntVar(value=12)
        self.fpslim_slider = ttk.Scale(ctrl, from_=1, to=30, variable=self.fpslim_var,
                                       command=self._on_fpslim_change)
        self.fpslim_slider.grid(row=3, column=1, sticky="ew")
        self.fpslim_label = ttk.Label(ctrl, text="12", width=5)
        self.fpslim_label.grid(row=3, column=2, padx=(4, 0))

    def _build_colors_panel(self):
        frame = ttk.LabelFrame(self.root, text="Screen Colors")
        frame.grid(row=1, column=1, sticky="nsew", padx=3, pady=3)
        frame.columnconfigure(0, weight=1)

        # Prevalence stacked bar
        ttk.Label(frame, text="Screen Composition", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=6, pady=(4, 0))
        self.prevalence_canvas = tk.Canvas(frame, bg=CANVAS_BG, height=28, highlightthickness=0)
        self.prevalence_canvas.grid(row=1, column=0, sticky="ew", padx=6, pady=(2, 6))

        # Accent colors header
        ttk.Label(frame, text="Accent Colors (scored)", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky="w", padx=6, pady=(0, 2))

        # Scrollable color list
        self.colors_frame = ttk.Frame(frame)
        self.colors_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 4))
        frame.rowconfigure(3, weight=1)
        self.colors_frame.columnconfigure(0, weight=1)
        self._color_widgets: List[dict] = []

        # Create 8 color item slots
        for i in range(8):
            row_frame = ttk.Frame(self.colors_frame)
            row_frame.grid(row=i, column=0, sticky="ew", pady=1)
            row_frame.columnconfigure(2, weight=1)

            swatch = tk.Canvas(row_frame, width=28, height=22, bg="#333",
                               highlightthickness=1, highlightbackground="#555")
            swatch.grid(row=0, column=0, padx=(0, 6))

            hex_lbl = ttk.Label(row_frame, text="-------", font=("Consolas", 9), width=8)
            hex_lbl.grid(row=0, column=1, padx=(0, 4))

            bar_canvas = tk.Canvas(row_frame, height=18, bg="#222", highlightthickness=0)
            bar_canvas.grid(row=0, column=2, sticky="ew", padx=(0, 4))

            pct_lbl = ttk.Label(row_frame, text="", font=("Consolas", 9), width=6)
            pct_lbl.grid(row=0, column=3)

            score_lbl = ttk.Label(row_frame, text="", font=("Consolas", 8), width=8)
            score_lbl.grid(row=0, column=4, padx=(2, 0))

            item = {"frame": row_frame, "swatch": swatch, "hex_lbl": hex_lbl,
                    "bar_canvas": bar_canvas, "pct_lbl": pct_lbl, "score_lbl": score_lbl,
                    "hex": None}
            # Click to select
            for widget in (row_frame, swatch, hex_lbl, bar_canvas, pct_lbl, score_lbl):
                widget.bind("<Button-1>", lambda e, idx=i: self._on_color_item_click(idx))
            self._color_widgets.append(item)

    def _build_right_panel(self):
        frame = ttk.Frame(self.root)
        frame.grid(row=1, column=2, sticky="nsew", padx=(3, 8), pady=3)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)

        # Color Map
        map_frame = ttk.LabelFrame(frame, text="Color Map (Hue x Saturation)")
        map_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        map_frame.columnconfigure(0, weight=1)

        self.colormap_canvas = tk.Canvas(map_frame, bg=CANVAS_BG,
                                         width=COLORMAP_W, height=COLORMAP_H,
                                         highlightthickness=0)
        self.colormap_canvas.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.colormap_canvas.bind("<Button-1>", self._on_colormap_click)

        bri_frame = ttk.Frame(map_frame)
        bri_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 4))
        bri_frame.columnconfigure(1, weight=1)
        ttk.Label(bri_frame, text="Brightness:").grid(row=0, column=0, padx=(0, 4))
        self.map_bri_var = tk.DoubleVar(value=0.85)
        bri_slider = ttk.Scale(bri_frame, from_=0.1, to=1.0, variable=self.map_bri_var,
                               command=self._on_map_brightness_change)
        bri_slider.grid(row=0, column=1, sticky="ew")
        self.map_bri_label = ttk.Label(bri_frame, text="85%", width=5)
        self.map_bri_label.grid(row=0, column=2, padx=(4, 0))

        # Color Info
        info_frame = ttk.LabelFrame(frame, text="Color Analysis")
        info_frame.grid(row=1, column=0, sticky="nsew", pady=(3, 0))
        info_frame.columnconfigure(0, weight=1)

        # Selected color swatch + label
        top_info = ttk.Frame(info_frame)
        top_info.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))

        self.info_swatch = tk.Canvas(top_info, width=48, height=36, bg="#333",
                                     highlightthickness=1, highlightbackground="#666")
        self.info_swatch.pack(side="left", padx=(0, 10))

        lbl_frame = ttk.Frame(top_info)
        lbl_frame.pack(side="left", fill="x", expand=True)
        self.info_hex_var = tk.StringVar(value="Click a color to analyze")
        self.info_cat_var = tk.StringVar(value="")
        self.info_hsv_var = tk.StringVar(value="")
        ttk.Label(lbl_frame, textvariable=self.info_hex_var,
                  font=("Consolas", 11, "bold")).pack(anchor="w")
        ttk.Label(lbl_frame, textvariable=self.info_cat_var,
                  font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Label(lbl_frame, textvariable=self.info_hsv_var,
                  font=("Consolas", 9)).pack(anchor="w")

        # Score breakdown
        ttk.Separator(info_frame, orient="horizontal").grid(
            row=1, column=0, sticky="ew", padx=6, pady=2)

        self.score_text = tk.Text(info_frame, height=12, width=38, font=("Consolas", 9),
                                  bg="#1e1e2e", fg="#cccccc", relief="flat",
                                  highlightthickness=0, state="disabled",
                                  wrap="word", padx=6, pady=4)
        self.score_text.grid(row=2, column=0, sticky="nsew", padx=6, pady=(2, 6))
        info_frame.rowconfigure(2, weight=1)

        # Configure text tags for colored scores
        self.score_text.tag_configure("header", foreground="#e0e0e0", font=("Consolas", 10, "bold"))
        self.score_text.tag_configure("good", foreground="#50fa7b")
        self.score_text.tag_configure("ok", foreground="#f1fa8c")
        self.score_text.tag_configure("bad", foreground="#ff5555")
        self.score_text.tag_configure("label", foreground="#8888aa")
        self.score_text.tag_configure("value", foreground="#cccccc")

    def _build_history_panel(self):
        frame = ttk.LabelFrame(self.root, text="Color History (5s)")
        frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(8, 3), pady=(3, 8))
        frame.columnconfigure(0, weight=1)

        self.history_canvas = tk.Canvas(frame, bg=CANVAS_BG, height=HISTORY_H,
                                        highlightthickness=0)
        self.history_canvas.grid(row=0, column=0, sticky="ew", padx=4, pady=4)

    def _build_sim_panel(self):
        frame = ttk.LabelFrame(self.root, text="Live Simulation")
        frame.grid(row=2, column=2, sticky="nsew", padx=(3, 8), pady=(3, 8))
        frame.columnconfigure(0, weight=1)

        # Smooth lamp
        sim_top = ttk.Frame(frame)
        sim_top.pack(fill="x", padx=6, pady=(6, 2))

        ttk.Label(sim_top, text="Output (smoothed):", font=("Segoe UI", 9)).pack(anchor="w")
        self.sim_canvas = tk.Canvas(sim_top, bg=CANVAS_BG, width=SIM_SIZE + 20,
                                    height=SIM_SIZE + 10, highlightthickness=0)
        self.sim_canvas.pack(pady=(2, 0))
        self.sim_hex_var = tk.StringVar(value="#000000")
        ttk.Label(sim_top, textvariable=self.sim_hex_var, font=("Consolas", 10)).pack()

        # Raw vs Smooth comparison
        cmp_frame = ttk.Frame(frame)
        cmp_frame.pack(fill="x", padx=6, pady=(4, 2))

        ttk.Label(cmp_frame, text="Raw:", font=("Segoe UI", 8)).grid(row=0, column=0, padx=(0, 4))
        self.raw_swatch = tk.Canvas(cmp_frame, width=30, height=20, bg="#333",
                                    highlightthickness=1, highlightbackground="#555")
        self.raw_swatch.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(cmp_frame, text="Smooth:", font=("Segoe UI", 8)).grid(row=0, column=2, padx=(0, 4))
        self.smooth_swatch = tk.Canvas(cmp_frame, width=30, height=20, bg="#333",
                                       highlightthickness=1, highlightbackground="#555")
        self.smooth_swatch.grid(row=0, column=3)

        # Send indicator
        self.send_var = tk.StringVar(value="")
        self.send_label = ttk.Label(frame, textvariable=self.send_var,
                                    font=("Consolas", 9))
        self.send_label.pack(padx=6, pady=(2, 6))

    # ── Initialization helpers ───────────────────────────────────────────

    def _draw_placeholder(self):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            PREVIEW_W // 2, PREVIEW_H // 2,
            text="Click \u25b6 Start to begin capture",
            fill="#555555", font=("Segoe UI", 12))

    def _populate_monitors(self):
        monitors = self.engine.get_monitors()
        self.monitor_cb["values"] = monitors
        if monitors:
            self.monitor_cb.current(min(1, len(monitors) - 1))

    def _generate_colormap(self):
        cw = self.colormap_canvas.winfo_reqwidth() or COLORMAP_W
        ch = self.colormap_canvas.winfo_reqheight() or COLORMAP_H
        arr = generate_colormap_array(cw, ch, self._colormap_value)
        img = Image.fromarray(arr)
        self._colormap_base_photo = ImageTk.PhotoImage(img)
        self.colormap_canvas.delete("all")
        self.colormap_canvas.create_image(0, 0, anchor="nw", image=self._colormap_base_photo)

    # ── Main Update Loop ─────────────────────────────────────────────────

    def _update_loop(self):
        if self.engine.running:
            with self.engine.lock:
                has_data = self.engine.new_data
                self.engine.new_data = False
                lamp_color = self.engine.pending_lamp_color
                self.engine.pending_lamp_color = None

            if has_data:
                self._update_preview()
                self._update_colors()
                self._update_colormap_markers()
                self._update_simulation()

            # Send color to lamp if enabled
            if lamp_color and self.lamp_send_enabled and self.lamp_connected:
                self._send_color_to_lamp(lamp_color)

            self._update_history()
            self.fps_var.set(f"FPS: {self.engine.fps_actual:.1f}")
            self.status_var.set("Running")
        else:
            self.status_var.set("Stopped")

        self.root.after(50, self._update_loop)

    # ── UI Update Methods ────────────────────────────────────────────────

    def _update_preview(self):
        with self.engine.lock:
            frame = self.engine.latest_frame
        if frame is None:
            return

        h, w = frame.shape[:2]
        canvas_w = max(self.preview_canvas.winfo_width(), PREVIEW_W)
        canvas_h = max(self.preview_canvas.winfo_height(), PREVIEW_H)

        # Fit to canvas
        scale = min(canvas_w / w, canvas_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Draw crop overlay
        crop = self.engine.crop_percent / 100.0
        my = int(new_h * crop)
        mx = int(new_w * crop)

        if crop > 0:
            overlay = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            dark = (0, 0, 0, 120)
            # Top
            draw.rectangle([0, 0, new_w, my], fill=dark)
            # Bottom
            draw.rectangle([0, new_h - my, new_w, new_h], fill=dark)
            # Left
            draw.rectangle([0, my, mx, new_h - my], fill=dark)
            # Right
            draw.rectangle([new_w - mx, my, new_w, new_h - my], fill=dark)
            # Border around active area
            draw.rectangle([mx, my, new_w - mx - 1, new_h - my - 1],
                           outline=(255, 220, 0, 200), width=2)

            img_rgba = img.convert("RGBA")
            img = Image.alpha_composite(img_rgba, overlay).convert("RGB")

        self._preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        ox = (canvas_w - new_w) // 2
        oy = (canvas_h - new_h) // 2
        self.preview_canvas.create_image(ox, oy, anchor="nw", image=self._preview_photo)

        # Store mapping for click sampling
        self._preview_offset = (ox, oy)
        self._preview_scale = scale
        self._preview_img_size = (w, h)

    def _update_colors(self):
        with self.engine.lock:
            all_cols = list(self.engine.all_colors)
            dom_cols = list(self.engine.dominant_colors)

        # Prevalence stacked bar
        self.prevalence_canvas.delete("all")
        cw = max(self.prevalence_canvas.winfo_width(), 200)
        ch = 28
        x = 0
        total_pct = sum(pct for _, pct in all_cols)
        for hex_color, pct in all_cols:
            w = max(1, int(pct / max(total_pct, 1) * cw))
            self.prevalence_canvas.create_rectangle(x, 0, x + w, ch, fill=hex_color, outline="")
            x += w
        if x < cw:
            self.prevalence_canvas.create_rectangle(x, 0, cw, ch, fill="#333333", outline="")

        # Accent colors list
        max_pct = max((pct for _, pct in dom_cols), default=1)
        for i, item in enumerate(self._color_widgets):
            if i < len(dom_cols):
                hex_color, pct = dom_cols[i]
                score_info = calculate_score_breakdown(hex_color, pct)
                item["hex"] = hex_color

                # Swatch
                item["swatch"].configure(bg=hex_color)

                # Hex label
                item["hex_lbl"].configure(text=hex_color)

                # Proportion bar
                bar_w = max(item["bar_canvas"].winfo_width(), 80)
                item["bar_canvas"].delete("all")
                fill_w = int(pct / max(max_pct, 1) * bar_w)
                item["bar_canvas"].create_rectangle(0, 0, fill_w, 18,
                                                    fill=hex_color, outline="")

                # Percentage
                item["pct_lbl"].configure(text=f"{pct:.1f}%")

                # Score
                total = score_info["total"]
                tag = "good" if total >= 60 else ("ok" if total >= 30 else "bad")
                color = {"good": "#50fa7b", "ok": "#f1fa8c", "bad": "#ff5555"}[tag]
                item["score_lbl"].configure(text=f"S:{total:.0f}", foreground=color)

                item["frame"].grid()
            else:
                item["hex"] = None
                item["swatch"].configure(bg="#333")
                item["hex_lbl"].configure(text="")
                item["bar_canvas"].delete("all")
                item["pct_lbl"].configure(text="")
                item["score_lbl"].configure(text="")
                item["frame"].grid_remove()

    def _update_colormap_markers(self):
        self.colormap_canvas.delete("marker")
        with self.engine.lock:
            dom_cols = list(self.engine.dominant_colors)
            smooth = self.engine.current_smooth_hex

        cw = max(self.colormap_canvas.winfo_width(), COLORMAP_W)
        ch = max(self.colormap_canvas.winfo_height(), COLORMAP_H)

        # Draw accent color dots
        for hex_color, pct in dom_cols:
            h, s, v = hex_to_hsv(hex_color)
            x = h * cw
            y = (1 - s) * ch
            r = max(3, min(7, pct / 3))
            self.colormap_canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill=hex_color, outline="white", width=1.5, tags="marker")

        # Draw current output crosshair
        if smooth:
            h, s, v = hex_to_hsv(smooth)
            x = h * cw
            y = (1 - s) * ch
            size = 8
            self.colormap_canvas.create_line(x - size, y, x + size, y,
                                             fill="#ffffff", width=2, tags="marker")
            self.colormap_canvas.create_line(x, y - size, x, y + size,
                                             fill="#ffffff", width=2, tags="marker")
            self.colormap_canvas.create_oval(x - 4, y - 4, x + 4, y + 4,
                                             outline="#ffffff", width=2, tags="marker")

    def _update_history(self):
        self.history_canvas.delete("all")
        cw = max(self.history_canvas.winfo_width(), 400)
        ch = HISTORY_H
        now = time.time()
        window = 5.0  # seconds

        history = list(self.engine.color_history)
        if not history:
            self.history_canvas.create_text(
                cw // 2, ch // 2, text="Waiting for data...",
                fill="#555", font=("Segoe UI", 10))
            return

        # Draw color strips
        for i in range(len(history)):
            ts, hex_color = history[i]
            age = now - ts
            if age > window:
                continue
            x = (1 - age / window) * cw
            if i + 1 < len(history):
                next_ts = history[i + 1][0]
                next_age = now - next_ts
                if next_age > window:
                    x2 = 0
                else:
                    x2 = (1 - next_age / window) * cw
            else:
                x2 = cw
            if x2 > x:
                x, x2 = x2, x
            self.history_canvas.create_rectangle(
                int(x2), 0, int(x) + 1, ch, fill=hex_color, outline="")

        # Draw send event markers
        send_events = list(self.engine.send_events)
        for ts in send_events:
            age = now - ts
            if age > window:
                continue
            x = (1 - age / window) * cw
            self.history_canvas.create_line(
                int(x), ch - 8, int(x), ch, fill="#ffffff", width=2)
            self.history_canvas.create_polygon(
                int(x) - 3, ch - 8, int(x) + 3, ch - 8, int(x), ch - 3,
                fill="#ffffff", outline="")

        # Time axis labels
        for sec in range(0, 6):
            x = (1 - sec / window) * cw
            self.history_canvas.create_text(
                int(x), ch - 2, text=f"-{sec}s", fill="#666",
                font=("Consolas", 7), anchor="s")

    def _update_simulation(self):
        with self.engine.lock:
            raw_hex = self.engine.current_raw_hex or "#000000"
            smooth_hex = self.engine.current_smooth_hex or "#000000"
            would_send = self.engine.would_send

        # Main lamp circle
        self.sim_canvas.delete("all")
        cx = (SIM_SIZE + 20) // 2
        cy = (SIM_SIZE + 10) // 2
        r = SIM_SIZE // 2 - 4

        # Glow effect
        for i in range(3):
            gr = r + (3 - i) * 3
            try:
                rr, gg, bb = hex_to_rgb(smooth_hex)
                glow_hex = rgb_to_hex(max(0, rr // 3), max(0, gg // 3), max(0, bb // 3))
            except Exception:
                glow_hex = "#111111"
            self.sim_canvas.create_oval(cx - gr, cy - gr, cx + gr, cy + gr,
                                        fill="", outline=glow_hex, width=2)

        self.sim_canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    fill=smooth_hex, outline="#444", width=2)
        # Highlight
        self.sim_canvas.create_oval(cx - r // 2, cy - r // 2 - r // 4,
                                    cx, cy - r // 4,
                                    fill="", outline="#666666", width=1)

        self.sim_hex_var.set(smooth_hex)

        # Raw vs smooth swatches
        self.raw_swatch.configure(bg=raw_hex)
        self.smooth_swatch.configure(bg=smooth_hex)

        # Send indicator
        if would_send:
            if self.lamp_send_enabled and self.lamp_connected:
                self.send_var.set("\u2191 SENT to lamp")
                self.send_label.configure(foreground="#50fa7b")
            else:
                self.send_var.set("\u2191 Threshold exceeded")
                self.send_label.configure(foreground="#f1fa8c")
        else:
            self.send_var.set("-- below threshold --")
            self.send_label.configure(foreground="#666666")

    def _update_info_panel(self, hex_color: str, percentage: float = 0.0):
        """Update the color analysis panel for the selected color."""
        self.selected_color = hex_color
        r, g, b = hex_to_rgb(hex_color)
        h, s, v = hex_to_hsv(hex_color)
        h_deg = h * 360

        self.info_swatch.configure(bg=hex_color)
        self.info_hex_var.set(hex_color)
        self.info_cat_var.set(f"{get_hue_name(h_deg)} | RGB({r}, {g}, {b})")
        self.info_hsv_var.set(f"H:{h_deg:.0f}\u00b0  S:{s * 100:.0f}%  V:{v * 100:.0f}%")

        bd = calculate_score_breakdown(hex_color, percentage)

        self.score_text.configure(state="normal")
        self.score_text.delete("1.0", "end")

        if bd.get("rejected") and bd["total"] == 0 and bd["sat_score"] == 0:
            self.score_text.insert("end", "REJECTED\n", "bad")
            self.score_text.insert("end", bd.get("sat_reason", "Low quality"), "label")
            self.score_text.configure(state="disabled")
            return

        # Total score
        total = bd["total"]
        tag = "good" if total >= 60 else ("ok" if total >= 30 else "bad")
        self.score_text.insert("end", f"Ambient Score: {total:.1f}\n", "header")
        self.score_text.insert("end", "\u2500" * 32 + "\n", "label")

        # Components
        components = [
            ("Saturation", bd["sat_score"], 80, bd["sat_reason"]),
            ("Brightness", bd["bri_score"], 30, bd["bri_reason"]),
            ("Prevalence", bd["prev_score"], 25, bd["prev_reason"]),
            ("Hue Pref", bd["hue_score"], 20, bd["hue_reason"]),
        ]

        for name, score, max_val, reason in components:
            bar_len = 15
            if max_val > 0:
                filled = max(0, int(score / max_val * bar_len))
            else:
                filled = 0
            bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
            sc_tag = "good" if score >= max_val * 0.6 else ("ok" if score > 0 else "bad")
            self.score_text.insert("end", f"  {name:<12}", "label")
            self.score_text.insert("end", f"{bar} ", sc_tag)
            self.score_text.insert("end", f"{score:>5.1f}", sc_tag)
            self.score_text.insert("end", f" / {max_val}\n", "label")
            self.score_text.insert("end", f"{'':>14}{reason}\n", "value")

        # Penalties
        if bd["penalties"] != 0 or bd["penalty_reasons"]:
            pen = bd["penalties"]
            pen_tag = "bad" if pen < 0 else "good"
            self.score_text.insert("end", f"\n  {'Penalties':<12}", "label")
            self.score_text.insert("end", f"{pen:+.0f}\n", pen_tag)
            for pr in bd["penalty_reasons"]:
                self.score_text.insert("end", f"{'':>14}{pr}\n", "value")

        self.score_text.configure(state="disabled")

    # ── Event Handlers ───────────────────────────────────────────────────

    def _on_monitor_change(self, event=None):
        sel = self.monitor_cb.current()
        self.engine.monitor_index = sel

    def _on_mode_change(self, event=None):
        self.engine.mode = self.mode_var.get()

    def _on_crop_change(self, value=None):
        val = self.crop_var.get()
        self.engine.crop_percent = val
        self.crop_label.configure(text=f"{val}%")

    def _on_alpha_change(self, value=None):
        val = round(self.alpha_var.get(), 2)
        self.engine.alpha = val
        self.alpha_label.configure(text=f"{val:.2f}")

    def _on_thresh_change(self, value=None):
        val = round(self.thresh_var.get(), 3)
        self.engine.color_change_threshold = val
        self.thresh_label.configure(text=f"{val * 100:.1f}%")

    def _on_fpslim_change(self, value=None):
        val = self.fpslim_var.get()
        self.engine.fps_limit = val
        self.fpslim_label.configure(text=f"{val}")

    def _on_start_stop(self):
        if self.engine.running:
            self.engine.stop()
            self.start_btn.configure(text="\u25b6 Start")
        else:
            self.engine.start()
            self.start_btn.configure(text="\u23f8 Stop")

    def _on_color_item_click(self, idx: int):
        item = self._color_widgets[idx]
        if item["hex"]:
            # Find the percentage from dominant colors
            with self.engine.lock:
                dom = list(self.engine.dominant_colors)
            pct = 0.0
            for hx, p in dom:
                if hx == item["hex"]:
                    pct = p
                    break
            self._update_info_panel(item["hex"], pct)

    def _on_colormap_click(self, event):
        cw = max(self.colormap_canvas.winfo_width(), COLORMAP_W)
        ch = max(self.colormap_canvas.winfo_height(), COLORMAP_H)
        h = max(0, min(1, event.x / cw))
        s = max(0, min(1, 1 - event.y / ch))
        v = self._colormap_value

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        hex_color = rgb_to_hex(int(r * 255), int(g * 255), int(b * 255))
        self._update_info_panel(hex_color, 0.0)

    def _on_map_brightness_change(self, value=None):
        val = round(self.map_bri_var.get(), 2)
        self._colormap_value = val
        self.map_bri_label.configure(text=f"{int(val * 100)}%")
        self._generate_colormap()
        # Redraw markers if engine is running
        if self.engine.running:
            self._update_colormap_markers()

    def _on_preview_click(self, event):
        if not hasattr(self, "_preview_scale") or self.engine.latest_frame is None:
            return
        ox, oy = self._preview_offset
        scale = self._preview_scale
        w, h = self._preview_img_size

        img_x = int((event.x - ox) / scale)
        img_y = int((event.y - oy) / scale)

        if 0 <= img_x < w and 0 <= img_y < h:
            with self.engine.lock:
                frame = self.engine.latest_frame
            if frame is not None:
                r, g, b = frame[img_y, img_x]
                hex_color = rgb_to_hex(int(r), int(g), int(b))
                self._update_info_panel(hex_color, 0.0)

    def _on_preview_motion(self, event):
        if not hasattr(self, "_preview_scale") or self.engine.latest_frame is None:
            self._preview_hex_var.set("")
            return
        ox, oy = self._preview_offset
        scale = self._preview_scale
        w, h = self._preview_img_size

        img_x = int((event.x - ox) / scale)
        img_y = int((event.y - oy) / scale)

        if 0 <= img_x < w and 0 <= img_y < h:
            with self.engine.lock:
                frame = self.engine.latest_frame
            if frame is not None:
                r, g, b = frame[img_y, img_x]
                hex_color = rgb_to_hex(int(r), int(g), int(b))
                self._preview_hex_var.set(f"{hex_color}  ({img_x}, {img_y})  RGB({r}, {g}, {b})")
        else:
            self._preview_hex_var.set("")

    def _on_lamp_connect(self):
        """Connect or disconnect from the lamp."""
        if self.lamp_connected:
            self._lamp_disconnect()
            return

        if not LAMP_AVAILABLE:
            self.lamp_status_var.set("Missing tinytuya")
            return

        self.lamp_status_var.set("Connecting...")
        self.connect_btn.configure(state="disabled")
        self.root.update_idletasks()

        try:
            config_path = os.path.join(_BASE_DIR, "lamp_config.json")
            config = Config(config_path)
            dm = DeviceManager(config.device_config, config.data_points)
            ok = dm.connect()
            if ok:
                self.device_manager = dm
                self.lamp_connected = True
                self.connect_btn.configure(text="\U0001f7e2 Disconnect", state="normal")
                self.send_check.configure(state="normal")
                self.lamp_status_var.set("Connected")
                self.lamp_status_label.configure(foreground="#50fa7b")
                # Set colour mode so color commands work
                dm.set_mode("colour")
            else:
                dm.close()
                self.connect_btn.configure(state="normal")
                self.lamp_status_var.set("Connection failed")
                self.lamp_status_label.configure(foreground="#ff5555")
        except Exception as e:
            logger.error(f"Lamp connection error: {e}")
            self.connect_btn.configure(state="normal")
            self.lamp_status_var.set(f"Error: {e}")
            self.lamp_status_label.configure(foreground="#ff5555")

    def _lamp_disconnect(self):
        """Disconnect from the lamp."""
        self.lamp_send_enabled = False
        self.send_var_toggle.set(False)
        self.send_check.configure(state="disabled")
        if self.device_manager:
            try:
                self.device_manager.close()
            except Exception:
                pass
            self.device_manager = None
        self.lamp_connected = False
        self.connect_btn.configure(text="\u26ab Connect Lamp")
        self.lamp_status_var.set("Disconnected")
        self.lamp_status_label.configure(foreground="gray")

    def _on_send_toggle(self):
        self.lamp_send_enabled = self.send_var_toggle.get()

    def _send_color_to_lamp(self, hex_color: str):
        """Send a color to the connected lamp."""
        if not self.device_manager or not self.lamp_connected:
            return
        try:
            r, g, b = hex_to_rgb(hex_color)
            self.device_manager.set_color(r, g, b)
        except Exception as e:
            logger.error(f"Lamp send error: {e}")
            self.lamp_status_var.set(f"Send error")
            self.lamp_status_label.configure(foreground="#ff5555")

    def _on_close(self):
        self.engine.stop()
        if self.device_manager:
            try:
                self.device_manager.close()
            except Exception:
                pass
        self.root.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    if not CAPTURE_AVAILABLE:
        try:
            root = tk.Tk()
            root.withdraw()
            from tkinter import messagebox
            messagebox.showerror(
                "Missing Dependencies",
                "Screen capture requires: mss, numpy, Pillow\n\n"
                "Install with:\n  pip install mss numpy Pillow"
            )
            root.destroy()
        except Exception:
            print("ERROR: Required packages missing. Install with:")
            print("  pip install mss numpy Pillow")
        return

    root = tk.Tk()
    app = ScreenColorAnalyzerApp(root)
    root.protocol("WM_DELETE_WINDOW", app._on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
