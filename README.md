# Smart Lamp Controller - Improved Version

A modular and feature-rich application for controlling Tuya-based RGB smart lamps with advanced features including rainbow effects, music synchronization, and comprehensive configuration management.

## Features

### Core Functionality
- **Device Control**: Turn lamps on/off, adjust brightness and color temperature
- **Color Control**: Full RGB color selection with live preview
- **Multiple Modes**: White light and color light modes

### Advanced Effects
- **Rainbow Effects**: Customizable rainbow animations with speed and hue range controls
- **Music Synchronization**: Audio-reactive lighting with multiple modes:
  - RMS volume → brightness + color
  - RMS volume → brightness only
  - Beat detection → color changes
  - Frequency band analysis → rainbow effects
- **Real-time Visualization**: Live audio level and BPM display

### Improvements Over Original

#### 1. **Modular Architecture**
- **Separated Concerns**: Device management, audio processing, and effects are now separate modules
- **Clean Codebase**: Each component has a single responsibility
- **Better Maintainability**: Easier to modify and extend individual features

#### 2. **Enhanced Error Handling**
- **Proper Logging**: Structured logging with file output and console display
- **Graceful Degradation**: Features work even when optional dependencies are missing
- **Better Exception Handling**: Specific error types and recovery mechanisms

#### 3. **Configuration Management**
- **Persistent Settings**: User preferences saved between sessions
- **Flexible Configuration**: JSON-based config with defaults and validation
- **Device Management**: Easy device configuration and switching

#### 4. **Performance Optimizations**
- **Efficient Canvas Updates**: Optimized rainbow preview rendering
- **Thread Safety**: Proper synchronization between UI and worker threads
- **Resource Management**: Better cleanup and memory management

## Installation

### Prerequisites
- Python 3.7 or higher
- Tuya-compatible RGB smart lamp
- Local network access to the lamp

### Setup

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your device**:
   - Edit `lamp_config.json` (created on first run) or modify defaults in `config.py`
   - Update device ID, IP address, and local key

4. **Run the application**:
   ```bash
   python improved_lamp_controller.py
   ```

## Configuration

### Device Configuration
The application uses a JSON configuration file (`lamp_config.json`) that is automatically created with default values on first run. Key settings include:

```json
{
  "device": {
    "name": "Your Lamp Name",
    "id": "your_device_id",
    "address": "192.168.1.100",
    "local_key": "your_local_key",
    "version": "3.5"
  },
  "audio": {
    "sample_rate": 44100,
    "buffer_size": 1024,
    "default_sensitivity": 2.5
  },
  "effects": {
    "rainbow_speed": 50,
    "default_brightness": 500
  }
}
```

### Finding Device Information
1. **Device ID**: Use the original `lamp_controller.py` to discover devices
2. **IP Address**: Your lamp's local network IP
3. **Local Key**: Found in your Tuya Smart app or device documentation

## Usage

### Basic Controls
1. **Power**: Use the ON/OFF buttons to control the lamp
2. **White Light**: Adjust brightness and color temperature
3. **Static Color**: Choose any color using the color picker

### Effects
1. **Rainbow**: 
   - Adjust animation speed
   - Set hue range for custom color ranges
   - Start/stop with the rainbow button

2. **Music Sync**:
   - Select audio input device
   - Choose reactive mode
   - Adjust beat sensitivity
   - Start music synchronization

### Audio Setup
- **Windows**: Ensure microphone permissions are granted
- **macOS**: Grant microphone access in System Preferences
- **Linux**: Ensure your user is in the `audio` group

## Architecture

### Module Structure
```
lamp/
├── config.py              # Configuration management
├── device_manager.py       # Device communication
├── audio_processor.py     # Audio input processing
├── effects_engine.py       # Visual effects
├── logger_config.py        # Logging setup
├── improved_lamp_controller.py  # Main UI application
├── requirements.txt       # Dependencies
└── README.md             # This file
```

### Key Components

#### DeviceManager
- Handles all communication with Tuya devices
- Thread-safe command queue
- Connection management and status callbacks
- Automatic error recovery

#### AudioProcessor
- Real-time audio input processing
- Multiple audio analysis modes
- Device management and fallback handling
- BPM detection and frequency analysis

#### EffectsEngine
- Coordinates visual effects
- Rainbow animations with customizable parameters
- Audio-reactive effects
- Color management and transitions

#### Config
- Persistent configuration management
- Default value handling
- JSON-based storage with validation
- Runtime configuration updates

## Troubleshooting

### Common Issues

1. **Device Not Found**
   - Verify device is on same network
   - Check IP address and device ID
   - Ensure local key is correct

2. **Audio Not Working**
   - Install PyAudio: `pip install pyaudio`
   - Check microphone permissions
   - Verify audio device is not in use

3. **Permission Errors**
   - Run as administrator if needed
   - Check firewall settings
   - Ensure Python has network access

4. **Missing Dependencies**
   - Install all requirements: `pip install -r requirements.txt`
   - Some audio features require SciPy for frequency analysis

### Debug Mode
Enable debug logging by modifying the logging setup:
```python
setup_logging(log_level="DEBUG", log_file="logs/lamp_controller.log")
```

## Development

### Adding New Effects
1. Create effect methods in `EffectsEngine`
2. Add UI controls in the appropriate tab
3. Wire up callbacks in `setup_callbacks()`

### Supporting New Devices
1. Update device configuration in `config.py`
2. Modify data point mappings if needed
3. Test with the new device type

### Contributing
- Follow the modular architecture pattern
- Add proper error handling and logging
- Update configuration defaults for new features
- Test with and without optional dependencies

## License

This project is provided as-is for educational and personal use. Please respect the terms of service of any third-party services used.

## Changelog

### v2.0 (Improved Version)
- Complete modular rewrite
- Added configuration management
- Enhanced error handling and logging
- Improved audio processing
- Better performance and resource management
- Added comprehensive documentation

### v1.0 (Original)
- Basic device control
- Simple UI
- Device discovery
- Basic color control
