# Smart Lamp Controller - Executable

## Installation

No installation required! This is a standalone executable.

## Usage

1. Double-click `SmartLampController.exe` to run the application
2. Configure your lamp devices using the `lamp_config.json` file
3. The application will start with the GUI interface

## Configuration

Edit `lamp_config.json` to add your Tuya-compatible smart lamp devices:

```json
{
    "devices": [
        {
            "name": "Living Room Lamp",
            "ip": "192.168.1.100",
            "device_id": "your_device_id",
            "local_key": "your_local_key"
        }
    ]
}
```

## Requirements

- Windows 10 or later
- Network connection to control smart lamps
- Tuya-compatible smart lamp devices

## Troubleshooting

If you encounter issues:
1. Make sure your lamp devices are on the same network
2. Verify the device information in `lamp_config.json`
3. Check that your firewall allows the application to access the network

## Features

- Control multiple smart lamps
- Color picker and custom colors
- Brightness control
- Music synchronization (if audio devices available)
- API server for remote control
- Color history and presets

For detailed documentation, see `README_ORGANIZATION.md`.
