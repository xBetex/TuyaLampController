# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart Lamp Controller is a Python application for controlling Tuya-based RGB smart lamps. It provides a tkinter GUI, visual effects (rainbow, strobe, ambilight), music synchronization, and a REST API (port 8765) for external control. A companion Android app (`SmartLampApp/`) built with Kotlin/Jetpack Compose communicates via the REST API.

## Build and Run Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main GUI application
python smart_lamp_controller/main.py

# Run standalone GUI (from root lamp directory)
python improved_lamp_controller.py

# Run tests
pytest smart_lamp_controller/tests/

# Run a single test file
pytest smart_lamp_controller/tests/test_smart_ambient.py -v

# Pair a new lamp device
python smart_lamp_controller/scripts/pair_lamp.py

# Build Windows executable
python smart_lamp_controller/scripts/build.py
```

## Architecture

The project has two layers: standalone scripts at root (`improved_lamp_controller.py`, `local_lamp_gui.py`) and the organized `smart_lamp_controller/` package.

### Key Modules (smart_lamp_controller/)

- **`main.py`** — Entry point, wires everything together
- **`core/device_manager.py`** — Thread-safe Tuya device communication (see patterns below)
- **`core/effects_engine.py`** — Orchestrates effects, manages effect lifecycle
- **`core/effects/`** — Effect classes using template pattern (`BaseEffect` → `_loop()`)
- **`core/ambilight_processor.py`** — Screen capture with color change detection (3% RGB threshold, 12 FPS cap)
- **`core/smart_ambient_processor.py`** — Intelligent color selection with scoring/transparency
- **`core/audio_processor.py`** — Audio analysis (RMS, beat detection, frequency bands)
- **`src/improved_lamp_controller.py`** — Main tkinter GUI
- **`src/tabs/`** — Modular UI tabs inheriting from `BaseTab`
- **`src/api_server.py`** — REST API using stdlib `http.server` (no Flask/FastAPI)
- **`utils/config.py`** — JSON config with dot-notation access (`config.get('device.address')`)

### Android App (`SmartLampApp/`)
Kotlin/Jetpack Compose app using Retrofit to call the REST API. Cleartext HTTP allowed for local IPs (192.168.15.7, 10.0.2.2).

## Key Architectural Patterns

### Command Queue with Conflation (DeviceManager)
`DeviceManager` runs a daemon worker thread that processes commands from a priority queue:
- **Conflation**: Duplicate `set_colour` or `set_value` commands are merged — only the latest value is kept. This prevents device flooding from rapid slider changes.
- **Priority**: `send_command(..., urgent=True)` inserts at front of queue. `turn_off()` clears all pending color/value commands.
- **Queue overflow**: Capped at 100 commands, trimmed to 50 on overflow.
- **Condition variable**: Worker sleeps on `queue_condition`, woken by `send_command()`.

### Effect Template Pattern
Effects inherit `BaseEffect` and implement `_loop()`. The base class handles thread lifecycle, mode switching, callbacks, and brightness application. Check `self.running` in loops to support clean shutdown.

### Callback-Driven Architecture
Components communicate via registered callbacks rather than direct coupling:
```python
device_manager.add_status_callback(fn)      # Status text updates
device_manager.add_connection_callback(fn)   # Connection state changes
effect.add_color_callback(fn)               # Color preview for UI
```
Callback exceptions are caught and logged, never crash the caller.

### Graceful Degradation
Optional dependencies (pyaudio, numpy, scipy, mss, opencv-python) are imported with try/except. Audio and ambilight features are simply disabled when their dependencies are missing — the app still runs.

## Key Technical Details

### Device Communication
- Uses `tinytuya.BulbDevice` with Tuya protocol v3.5
- Persistent socket connection (`set_socketPersistent(True)`)
- DPS mapping: power=20, mode=21, brightness=22, temperature=23, scene=25
- Auto key refresh on connection failure (tries empty key re-pairing)

### Value Ranges
- RGB: 0-255 per channel
- Brightness/temperature: 0-1000 (device scale)
- Effect speed: 1-100
- Hue: 0.0-1.0 (Python `colorsys` convention)

### REST API (port 8765)
- Pure stdlib `http.server`, no external dependencies
- CORS enabled (all origins)
- All endpoints are POST except `GET /status`
- Shared state via class variables on `LampApiHandler` (device_manager, effects_engine)
- Runs in daemon thread via `start_api_server()`

### Configuration
- `lamp_config.json` stores device credentials (device_id, local_key, IP)
- `Config` class merges with hardcoded defaults for missing keys
- Config persists changes back to JSON file

## Common Patterns

- Use `send_command()` with `urgent=True` for power operations
- Call `stop_all_effects()` before shutdown or power off
- Effects run in daemon threads — always check `self.running` in loops
- Tab components inherit `BaseTab` for consistent layout with `ScrollableFrame`
- Use `_notify_color(hex)` in effects to update UI color preview
- AmbilightProcessor uses exponential smoothing (alpha 0.15-0.3) and color change detection to reduce device commands
