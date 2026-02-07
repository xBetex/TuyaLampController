# Why You Cannot Connect and Turn Off Your Lamp

## 🔍 Problem Identified

Your lamp **requires a `local_key` (authentication secret)** to control it. Without this key, you can connect to the device but all control commands will fail with:

```
Error: "Check device key or version"
Error Code: 914
```

## ✅ What's Working

- ✅ Network connectivity (ping works)
- ✅ Port 6668 is open and accessible
- ✅ Device discovery works (found device ID: `YOUR_DEVICE_ID`)
- ✅ Connection can be established
- ❌ **Control commands fail** (missing authentication key)

## 🔑 Solution: Get Your Local Key

You need to obtain your device's `local_key` to authenticate commands. Here are the methods:

### Method 1: tinytuya Wizard (Easiest - Recommended)

```bash
python -m tinytuya wizard
```

This will:
1. Scan your network for Tuya devices
2. Guide you through getting the local_key
3. Save credentials to a JSON file

After running, check the generated JSON file for your device's `key` or `local_key`.

### Method 2: Tuya IoT Platform (Official)

1. Go to https://iot.tuya.com/
2. Create a free account
3. Create a Cloud Project
4. Link your device
5. Find your device in Device Management
6. Look for "Local Key" or "Device Secret"

### Method 3: Extract from Tuya Smart App (Advanced)

Requires root/jailbreak access to extract from the app's database.

## 📝 How to Use the Key Once You Have It

Once you have your `local_key`, use it like this:

```python
import tinytuya

# Your device info
lamp_ip = "YOUR_DEVICE_IP"
lamp_id = "YOUR_DEVICE_ID"
version = "3.5"
local_key = "your_actual_key_here"  # <-- Your key goes here

# Create device and set the key
d = tinytuya.Device(lamp_id, lamp_ip)
d.set_version(version)
d.set_key(local_key)  # <-- This is the crucial line!

# Now you can control it
d.turn_off()  # This will work now!
d.turn_on()
```

## 📄 Files Created

1. **`diagnose_connection.py`** - Diagnostic tool that identified the issue
2. **`get_local_key.py`** - Guide on how to get your local_key
3. **`working_lamp_control.py`** - Working example (just add your key)

## 🚀 Quick Start

1. Run: `python -m tinytuya wizard`
2. Follow the prompts to get your local_key
3. Open `working_lamp_control.py`
4. Replace `YOUR_LOCAL_KEY_HERE` with your actual key
5. Run: `python working_lamp_control.py`

## ⚠️ Important Notes

- The `local_key` is device-specific and unique to your lamp
- Modern Tuya devices don't use default keys
- The key is required for **all** control commands (on/off, brightness, color, etc.)
- Without the key, you can discover and connect, but cannot control

## 🔧 Alternative Solutions

If you cannot get the local_key:

1. **Use Tuya Cloud API** - Requires API credentials from Tuya IoT Platform
2. **Use Google Home Integration** - If your lamp is linked to Google Home
3. **Check if LAN Control is enabled** - Some devices need this enabled in the Tuya Smart app

## 📊 Test Results Summary

From the full test suite:
- ✅ Network: PASSED
- ✅ Discovery: PASSED (found device)
- ✅ Connection: PASSED (can connect)
- ❌ Control: FAILED (missing local_key)

The diagnostic clearly shows: **"Check device key or version"** - this means you need the `local_key`.
