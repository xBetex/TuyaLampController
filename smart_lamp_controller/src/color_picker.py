import tkinter as tk
from tkinter import ttk, colorchooser
from typing import Optional, List, Tuple
import colorsys
import time
try:
    from color_history import HIST
except Exception:
    from collections import deque
    class _LocalHistory:
        def __init__(self):
            self._buf = deque(maxlen=10)
            self._subs = []
        def add(self, direction, color, message):
            import time as _t
            ts = _t.strftime("%H:%M:%S")
            self._buf.append((ts, direction, (color or "").lower(), message))
            for cb in list(self._subs):
                try:
                    cb(list(self._buf))
                except Exception:
                    pass
        def subscribe(self, cb):
            if cb not in self._subs:
                self._subs.append(cb)
                try:
                    cb(list(self._buf))
                except Exception:
                    pass
        def unsubscribe(self, cb):
            try:
                self._subs.remove(cb)
            except Exception:
                pass
    HIST = _LocalHistory()


class ColorPicker:
    def __init__(self, parent, device_manager, effects_engine):
        self.parent = parent
        self.device_manager = device_manager
        self.effects_engine = effects_engine

        self.window = tk.Toplevel(parent)
        self.window.title("Color Picker")
        self.window.geometry("780x560")
        self.window.minsize(640, 460)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.selected_color = "#ff0000"
        self._auto_running = False
        self._auto_after_id: Optional[str] = None
        self._auto_interval = 0.5

        root = ttk.Frame(self.window, padding=14)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Color Picker", font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)
        ttk.Button(header, text="Close", command=self.on_close).pack(side=tk.RIGHT)

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

        presets_frame = ttk.LabelFrame(body, text="Preset Colors", padding=10)
        presets_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_presets(presets_frame)

        mid = ttk.LabelFrame(body, text="Preview & Info", padding=10)
        mid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 10))
        self.preview_canvas = tk.Canvas(mid, width=240, height=240, bg="#111111", highlightthickness=0)
        self.preview_canvas.pack(pady=(0, 8))
        self.preview_bulb = self.preview_canvas.create_oval(20, 20, 220, 220, fill=self.selected_color, outline="#333333", width=2)

        self.hex_var = tk.StringVar(value=self.selected_color.upper())
        self.rgb_var = tk.StringVar(value="RGB: 255, 0, 0")
        self.hsv_var = tk.StringVar(value="HSV: 0.00, 1.00, 1.00")

        ttk.Label(mid, textvariable=self.hex_var, font=("Consolas", 12, "bold")).pack(anchor=tk.W)
        ttk.Label(mid, textvariable=self.rgb_var).pack(anchor=tk.W)
        ttk.Label(mid, textvariable=self.hsv_var).pack(anchor=tk.W)

        controls = ttk.Frame(mid)
        controls.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(controls, text="Custom Color 🎨", command=self.choose_custom_color).pack(side=tk.LEFT)
        ttk.Button(controls, text="Apply Now 💡", command=self.apply_color).pack(side=tk.RIGHT)

        right = ttk.LabelFrame(body, text="History & Auto Mode", padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        hist_container = ttk.Frame(right)
        hist_container.pack(fill=tk.BOTH, expand=True)
        self.history_text = tk.Text(hist_container, height=12, width=32, wrap="none", font=("Consolas", 9))
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vscroll = ttk.Scrollbar(hist_container, orient=tk.VERTICAL, command=self.history_text.yview)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.configure(yscrollcommand=vscroll.set)

        auto_frame = ttk.Frame(right)
        auto_frame.pack(fill=tk.X, pady=(10, 0))
        self.auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(auto_frame, text="Automatic Mode (send to lamp)", variable=self.auto_var, command=self._toggle_auto).pack(anchor=tk.W)
        rate_row = ttk.Frame(auto_frame)
        rate_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(rate_row, text="Rate (seconds):").pack(side=tk.LEFT)
        self.rate_var = tk.DoubleVar(value=self._auto_interval)
        rate_scale = ttk.Scale(rate_row, from_=0.1, to=3.0, variable=self.rate_var, orient=tk.HORIZONTAL, command=lambda _: self._on_rate_change())
        rate_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
        self.rate_label = ttk.Label(rate_row, text=f"{self._auto_interval:.2f}s")
        self.rate_label.pack(side=tk.RIGHT)

        mode_row = ttk.Frame(auto_frame)
        mode_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(mode_row, text="Mode:").pack(side=tk.LEFT)
        self.mode_combo = ttk.Combobox(mode_row, state="readonly", values=[
            "Accurate (slower)",
            "Balanced",
            "Responsive (faster)"
        ])
        self.mode_combo.current(1)
        self.mode_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        try:
            HIST.subscribe(self._on_history_update)
        except Exception:
            pass

        self._update_info_labels(self.selected_color)
        self._render_preview(self.selected_color)

    def _build_presets(self, parent):
        colors: List[Tuple[str, str]] = [
            ("Red", "#ff0000"), ("Orange", "#ff7f00"), ("Yellow", "#ffff00"), ("Lime", "#7fff00"),
            ("Green", "#00ff00"), ("Cyan", "#00ffff"), ("Blue", "#0000ff"), ("Violet", "#8b00ff"),
            ("Magenta", "#ff00ff"), ("Pink", "#ff66cc"), ("White", "#ffffff"), ("Warm", "#ffcc80"),
            ("Cool", "#80ccff"), ("Amber", "#ffbf00"), ("Teal", "#008080"), ("Purple", "#800080"),
        ]
        grid = ttk.Frame(parent)
        grid.pack(fill=tk.BOTH, expand=True)
        cols = 4
        for i, (name, col) in enumerate(colors):
            r, c = divmod(i, cols)
            cell = ttk.Frame(grid, padding=2)
            cell.grid(row=r, column=c, sticky=tk.NSEW)
            sw = tk.Button(cell, width=4, height=2, bg=col, relief="raised", bd=2, command=lambda c=col: self._select_color(c))
            sw.pack(side=tk.TOP, pady=(0, 2))
            ttk.Label(cell, text=name, font=("Segoe UI", 8)).pack()
        for i in range(cols):
            grid.columnconfigure(i, weight=1)

    def _select_color(self, color_hex: str):
        self.selected_color = color_hex
        self._update_info_labels(color_hex)
        self._render_preview(color_hex)
        self._log("PICK", color_hex, "Preset selected")
        if self._auto_running:
            self._send_color(color_hex)

    def _update_info_labels(self, color_hex: str):
        try:
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            self.hex_var.set(color_hex.upper())
            self.rgb_var.set(f"RGB: {r}, {g}, {b}")
            h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
            self.hsv_var.set(f"HSV: {h*360:.2f}°, {s:.2f}, {v:.2f}")
        except Exception:
            pass

    def _render_preview(self, color_hex: str):
        try:
            self.preview_canvas.itemconfig(self.preview_bulb, fill=color_hex, outline=color_hex)
        except Exception:
            pass

    def choose_custom_color(self):
        color = colorchooser.askcolor(title="Choose Color", initialcolor=self.selected_color)
        if color and color[1]:
            self._select_color(color[1])

    def apply_color(self):
        self._send_color(self.selected_color)

    def _send_color(self, color_hex: str):
        if not self.device_manager.is_connected:
            return
        try:
            if hasattr(self.device_manager, "set_mode"):
                self.device_manager.set_mode("colour")
            self.effects_engine.stop_all_effects()
            self.effects_engine.set_color_from_hex(color_hex, 1.0)
            self._log("OUT", color_hex, "Applied to lamp")
        except Exception as e:
            self._log("ERR", color_hex, f"Apply failed: {e}")

    def _toggle_auto(self):
        self._auto_running = bool(self.auto_var.get())
        if self._auto_running:
            self._schedule_auto()
        else:
            if self._auto_after_id:
                try:
                    self.window.after_cancel(self._auto_after_id)
                except Exception:
                    pass
                self._auto_after_id = None

    def _on_rate_change(self):
        try:
            self._auto_interval = max(0.1, min(5.0, float(self.rate_var.get())))
        except Exception:
            self._auto_interval = 0.5
        self.rate_label.config(text=f"{self._auto_interval:.2f}s")

    def _on_mode_change(self, event=None):
        mode = self.mode_combo.get()
        if mode.startswith("Accurate"):
            self._auto_interval = 1.0
        elif mode.startswith("Responsive"):
            self._auto_interval = 0.2
        else:
            self._auto_interval = 0.5
        self.rate_var.set(self._auto_interval)
        self.rate_label.config(text=f"{self._auto_interval:.2f}s")

    def _schedule_auto(self):
        if not self._auto_running:
            return
        self._send_color(self.selected_color)
        self._auto_after_id = self.window.after(int(self._auto_interval * 1000), self._schedule_auto)

    def _on_history_update(self, entries):
        if not hasattr(self, "history_text"):
            return
        try:
            t = self.history_text
            t.configure(state=tk.NORMAL)
            t.delete("1.0", tk.END)
            for ts_i, dir_i, col_i, msg_i in entries:
                if col_i and isinstance(col_i, str) and col_i.startswith('#') and len(col_i) == 7:
                    tag = f"swatch_{col_i}"
                    if tag not in t.tag_names():
                        try:
                            r = int(col_i[1:3], 16); g = int(col_i[3:5], 16); b = int(col_i[5:7], 16)
                            luminance = 0.2126*r + 0.7152*g + 0.0722*b
                            fg = '#000000' if luminance > 160 else '#ffffff'
                            t.tag_configure(tag, background=col_i, foreground=fg)
                        except Exception:
                            tag = None
                    if tag in t.tag_names():
                        t.insert(tk.END, '   ', tag)
                        t.insert(tk.END, ' ')
                line_txt = f"[{ts_i}] {dir_i:<3} {col_i:<8} {msg_i}"
                t.insert(tk.END, line_txt + "\n")
            t.see(tk.END)
            t.configure(state=tk.DISABLED)
        except Exception:
            pass

    def _log(self, direction: str, color: str, message: str):
        try:
            HIST.add(direction, color, message)
        except Exception:
            pass

    def on_close(self):
        try:
            if self._auto_after_id:
                self.window.after_cancel(self._auto_after_id)
        except Exception:
            pass
        try:
            HIST.unsubscribe(self._on_history_update)
        except Exception:
            pass
        self.window.destroy()


def open_color_picker(parent, device_manager, effects_engine):
    return ColorPicker(parent, device_manager, effects_engine)


def main():
    class DummyDevice:
        def __init__(self):
            self.is_connected = True
        def set_mode(self, m):
            pass
        def turn_on(self):
            pass
        def turn_off(self):
            pass
    class DummyEffects:
        def stop_all_effects(self):
            pass
        def set_color_from_hex(self, hx, b):
            print(f"APPLY {hx}")
    root = tk.Tk()
    root.title("Color Picker")
    _ = ColorPicker(root, DummyDevice(), DummyEffects())
    try:
        root.mainloop()
    except KeyboardInterrupt:
        try:
            _.on_close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
