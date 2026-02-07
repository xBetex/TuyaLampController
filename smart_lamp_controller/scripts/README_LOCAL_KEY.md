# Local Key Fix for Smart Lamp Controller

This directory contains scripts to help you set up a persistent local key for your Tuya smart lamp, preventing the key from changing when you turn off the lamp.

## Problem
When you turn off your Tuya smart lamp, it may synchronize with a new local key, causing your controller to lose connection.

## Solutions

### 1. Local Key Fix Script
`local_key_fix.py` - Sets up a persistent local key that won't change

**Usage:**
```bash
cd scripts
python local_key_fix.py
```

**Options:**
1. Generate and set new persistent key
2. Set custom persistent key  
3. Test current connection
4. Force key update (re-pair)
5. View current configuration

### 2. Cloud API Manager
`cloud_api_manager.py` - Manages Tuya Cloud API for backup access

**Usage:**
```bash
cd scripts
python cloud_api_manager.py
```

**Options:**
1. Setup Cloud API credentials
2. Test Cloud API access
3. Generate curl command for device

## How It Works

### Local Key Fix
The script creates a persistent local key by:
1. Backing up your current configuration
2. Generating a new 16-character hex key
3. Updating the lamp_config.json file
4. Testing the connection with the new key

### Enhanced Device Manager
The core `device_manager.py` has been enhanced to:
1. Automatically attempt key refresh if connection fails
2. Save updated keys to the configuration file
3. Provide better error messages and logging

### Cloud API Backup
If local key issues persist, you can use Tuya's Cloud API as a backup:
1. Set up your Tuya Cloud credentials
2. Access your device through the cloud API
3. Generate curl commands for manual testing

## Quick Start

1. **Fix Local Key Issues:**
   ```bash
   python scripts/local_key_fix.py
   ```
   Choose option 1 to generate a new persistent key.

2. **Test Connection:**
   ```bash
   python scripts/local_key_fix.py
   ```
   Choose option 3 to test the connection.

3. **Set Up Cloud API (Optional):**
   ```bash
   python scripts/cloud_api_manager.py
   ```
   Choose option 1 to set up cloud credentials.

## Configuration Files

- `lamp_config.json` - Main device configuration
- `lamp_config_backup.json` - Automatic backup created by scripts

## Troubleshooting

### If the lamp still changes keys:
1. Use option 4 in `local_key_fix.py` to force key update
2. Try the cloud API as a backup method
3. Check if your lamp firmware needs updating

### If connection fails:
1. Verify the lamp is in pairing mode
2. Check your network connection
3. Try manual pairing with the original `pair_lamp.py` script

## Security Notes

- Local keys are stored in plain text in the configuration file
- Cloud API credentials should be kept secure
- Backups are created automatically for safety

## Support

For issues with:
- Local key problems: Use `local_key_fix.py`
- Cloud API access: Use `cloud_api_manager.py`
- General pairing: Use `pair_lamp.py`
