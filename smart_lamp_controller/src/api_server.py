"""
Minimal LAN REST API for Smart Lamp Controller (no music sync).
Uses Python stdlib http.server to avoid external dependencies.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from typing import Tuple

# Types are duck-typed; we expect device_manager and effects_engine

def _ok(data=None):
    return 200, {"ok": True, "data": data or {}}

def _bad(msg, code=400):
    return code, {"ok": False, "error": str(msg)}

class LampApiHandler(BaseHTTPRequestHandler):
    device_manager = None
    effects_engine = None

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        try:
            if self.path == "/status":
                connected = bool(self.device_manager.is_connected)
                resp = {
                    "connected": connected,
                }
                code, payload = _ok(resp)
                self._send(code, payload)
                return
            code, payload = _bad("Not Found", 404)
            self._send(code, payload)
        except Exception as e:
            code, payload = _bad(str(e), 500)
            self._send(code, payload)

    def do_POST(self):
        try:
            body = self._read_json()
            route = self.path
            dm = self.device_manager
            fx = self.effects_engine

            # Connection
            if route == "/connect":
                ok = dm.connect()
                code, payload = _ok({"connected": ok})
                self._send(code, payload)
                return
            if route == "/disconnect":
                dm.disconnect()
                code, payload = _ok({"connected": False})
                self._send(code, payload)
                return
            if route == "/check":
                ok = dm.check_connection()
                code, payload = _ok({"connected": ok})
                self._send(code, payload)
                return
            if route == "/reconnect":
                ok = dm.reconnect()
                code, payload = _ok({"connected": ok})
                self._send(code, payload)
                return

            # Power/Mode
            if route == "/power":
                on = bool(body.get("on", True))
                if on:
                    dm.turn_on()
                else:
                    # Stop all effects before priority shutdown
                    fx.stop_all_effects()
                    dm.turn_off()
                code, payload = _ok({"on": on})
                self._send(code, payload)
                return
            if route == "/mode":
                mode = body.get("mode", "white")
                dm.set_mode(mode)
                code, payload = _ok({"mode": mode})
                self._send(code, payload)
                return

            # White light controls
            if route == "/white":
                if "brightness" in body:
                    dm.set_brightness(int(body["brightness"]))
                if "temperature" in body:
                    dm.set_temperature(int(body["temperature"]))
                code, payload = _ok({"applied": True})
                self._send(code, payload)
                return

            # Static color
            if route == "/color":
                hex_color = body.get("hex")
                brightness = float(body.get("brightness", 1000)) / 1000.0
                if not hex_color:
                    code, payload = _bad("Missing 'hex' like #ff00aa")
                    self._send(code, payload)
                    return
                fx.set_color_from_hex(hex_color, brightness)
                code, payload = _ok({"hex": hex_color, "brightness": brightness})
                self._send(code, payload)
                return

            # Effects: Rainbow
            if route == "/effects/rainbow/start":
                speed = float(body.get("speed", 50))
                h_min = float(body.get("h_min", 0.0))
                h_max = float(body.get("h_max", 1.0))
                use_custom = bool(body.get("use_custom", False))
                colors = body.get("colors", [])
                fx.set_rainbow_parameters(speed, h_min, h_max, colors, use_custom)
                fx.start_rainbow_effect()
                code, payload = _ok({"running": True})
                self._send(code, payload)
                return
            if route == "/effects/rainbow/stop":
                fx.stop_rainbow_effect()
                code, payload = _ok({"running": False})
                self._send(code, payload)
                return

            # Effects: Strobe
            if route == "/effects/strobe/start":
                speed = float(body.get("speed", 80))
                fx.set_strobe_parameters(speed)
                fx.start_strobe_effect()
                code, payload = _ok({"running": True})
                self._send(code, payload)
                return
            if route == "/effects/strobe/stop":
                fx.stop_strobe_effect()
                code, payload = _ok({"running": False})
                self._send(code, payload)
                return

            # Effects: White Strobe
            if route == "/effects/white_strobe/start":
                speed = float(body.get("speed", 80))
                fx.set_white_strobe_parameters(speed)
                fx.start_white_strobe_effect()
                code, payload = _ok({"running": True})
                self._send(code, payload)
                return
            if route == "/effects/white_strobe/stop":
                fx.stop_white_strobe_effect()
                code, payload = _ok({"running": False})
                self._send(code, payload)
                return

            # Effects: Ambilight
            if route == "/effects/ambilight/start":
                alpha = body.get("alpha")
                mode = body.get("mode")
                monitor = body.get("monitor_index")
                crop_percent = body.get("crop_percent")

                fx.set_ambilight_parameters(
                    alpha=float(alpha) if alpha is not None else None,
                    mode=mode,
                    monitor_index=int(monitor) if monitor is not None else None,
                    crop_percent=int(crop_percent) if crop_percent is not None else None
                )
                fx.start_ambilight_effect()
                code, payload = _ok({"running": True})
                self._send(code, payload)
                return

            # Update ambilight parameters while running
            if route == "/effects/ambilight/update":
                alpha = body.get("alpha")
                mode = body.get("mode")
                monitor = body.get("monitor_index")
                crop_percent = body.get("crop_percent")

                fx.set_ambilight_parameters(
                    alpha=float(alpha) if alpha is not None else None,
                    mode=mode,
                    monitor_index=int(monitor) if monitor is not None else None,
                    crop_percent=int(crop_percent) if crop_percent is not None else None
                )
                code, payload = _ok({"updated": True})
                self._send(code, payload)
                return
            if route == "/effects/ambilight/stop":
                fx.stop_ambilight_effect()
                code, payload = _ok({"running": False})
                self._send(code, payload)
                return

            # Effects: Smart Ambient
            if route == "/effects/smart_ambient/start":
                monitor = body.get("monitor_index")
                interval = body.get("update_interval")
                send_rate = body.get("send_rate_limit")

                fx.set_smart_ambient_parameters(
                    monitor_index=int(monitor) if monitor is not None else None,
                    update_interval=float(interval) if interval is not None else None,
                    send_rate_limit=float(send_rate) if send_rate is not None else None
                )
                success = fx.start_smart_ambient_effect()
                code, payload = _ok({"running": success})
                self._send(code, payload)
                return

            if route == "/effects/smart_ambient/stop":
                fx.stop_smart_ambient_effect()
                code, payload = _ok({"running": False})
                self._send(code, payload)
                return

            # Effects: Blinker
            if route == "/effects/blinker/start":
                speed = float(body.get("speed", 50))
                fx.set_blinker_parameters(speed)
                fx.start_blinker_effect()
                code, payload = _ok({"running": True})
                self._send(code, payload)
                return

            if route == "/effects/blinker/stop":
                fx.stop_blinker_effect()
                code, payload = _ok({"running": False})
                self._send(code, payload)
                return

            # Stop all effects
            if route == "/effects/stop_all":
                fx.stop_all_effects()
                code, payload = _ok({"stopped": True})
                self._send(code, payload)
                return

            # Get current effect status
            if route == "/effects/status":
                status = {
                    "active_effect": fx.active_effect,
                    "rainbow_running": fx.rainbow_running,
                    "blinker_running": fx.blinker_running,
                    "strobe_running": fx.strobe_running,
                    "white_strobe_running": fx.white_strobe_running,
                    "ambilight_running": fx.ambilight_running,
                    "smart_ambient_running": fx.smart_ambient_running,
                }
                code, payload = _ok(status)
                self._send(code, payload)
                return

            code, payload = _bad("Not Found", 404)
            self._send(code, payload)
        except Exception as e:
            code, payload = _bad(str(e), 500)
            self._send(code, payload)


def start_api_server(device_manager, effects_engine, host: str = "0.0.0.0", port: int = 8765):
    LampApiHandler.device_manager = device_manager
    LampApiHandler.effects_engine = effects_engine
    httpd = HTTPServer((host, port), LampApiHandler)

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread
