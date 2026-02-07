# Project Organization

This document describes the reorganized folder structure of the Smart Lamp Controller project.

## Folder Structure

```
smart_lamp_controller/
├── core/                    # Core functionality modules
│   ├── device_manager.py    # Device communication manager
│   ├── effects_engine.py    # Lighting effects and animations
│   ├── audio_processor.py   # Audio analysis and processing
│   ├── ambilight_processor.py # Ambient light processing
│   ├── smart_ambient_processor.py # Smart ambient processing
│   └── color_selection_logic.py # Color selection algorithms
│
├── src/                     # Main application modules
│   ├── color_picker.py      # Color picker interface
│   ├── color_map_window.py  # Main color mapping window
│   ├── improved_lamp_controller.py # Main lamp controller
│   ├── api_server.py        # REST API server
│   ├── pulsed_color_sender.py # Pulsed color sending
│   └── color_history.py     # Color history management
│
├── utils/                   # Utility modules
│   ├── config.py            # Configuration management
│   ├── logger_config.py     # Logging configuration
│   ├── demo_live_preview.py # Live preview demo
│   └── fix_indentation.py   # Code formatting utility
│
├── tests/                   # Test files
│   ├── test_*.py           # All test modules
│   └── ...                 # Individual test files
│
├── scripts/                 # Build and utility scripts
│   ├── pair_lamp.py        # Lamp pairing script
│   ├── build.py            # Build script
│   ├── build_simple.py     # Simple build script
│   └── setup.py            # Setup script
│
├── docs/                    # Documentation
│   ├── *.md                # All markdown documentation
│   └── ...                 # Individual doc files
│
├── logs/                    # Log files
│   └── lamp_controller.log # Application log
│
├── build/                   # Build output directory
├── __pycache__/            # Python cache
├── .git/                   # Git repository
├── .ruff_cache/            # Ruff cache
├── main.py                 # Application entry point
├── lamp_config.json        # Device configuration
├── requirements.txt        # Python dependencies
└── SmartLampController.spec # PyInstaller spec file
```

## Key Scripts

### Pairing Script (`scripts/pair_lamp.py`)
Use this script to pair your smart lamp when it's in pairing mode:

```bash
python scripts/pair_lamp.py
```

The script will:
1. Scan for Tuya devices on your network
2. Let you select which device to pair
3. Test the connection and basic controls
4. Save the configuration to `lamp_config.json`

### Main Application (`main.py`)
Run the main application after pairing:

```bash
python main.py
```

## Import Changes

Due to the reorganization, some import statements may need to be updated. The main modules now use relative imports from their respective folders.

## Configuration

The main configuration file `lamp_config.json` remains in the root directory for easy access.
