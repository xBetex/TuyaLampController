# Fix: tinytuya Wizard Permissions Error

## Problem

You ran `python -m tinytuya wizard` and it:
- ✅ Found your device ID: `YOUR_DEVICE_ID`
- ❌ Got error: "Code 28841001: 'No permissions.'"

## Why This Happens

The tinytuya wizard tries to get the `local_key` from Tuya Cloud API, but your project doesn't have the necessary permissions to access device details via API.

## Solutions

### ✅ Solution 1: Use Web Interface (Easiest - Recommended)

**This bypasses the API completely!**

1. Go to: https://iot.tuya.com/
2. Login with your account
3. Navigate to your project
4. Go to: **Device Management**
5. Find your Avant lamp (Device ID: `YOUR_DEVICE_ID`)
6. Click on the device
7. Look for:
   - "Local Key"
   - "Device Secret" 
   - "local_key"
   - "localKey"
8. Copy the value
9. Paste it into `avant_control.py`:
   ```python
   AVANT_KEY = "your_copied_key_here"
   ```

**This is the easiest method and doesn't need API permissions!**

### ✅ Solution 2: Fix Tuya IoT Platform Permissions

If you want to use the API, you need to fix permissions:

1. **Enable IoT Core Service**
   - Go to: Cloud → Services
   - Enable "IoT Core" (free tier available)
   - Some features may require subscription

2. **Link Your App Account**
   - Go to: Cloud → Authorization → Link App Account
   - Authorize your Tuya Smart app account
   - Make sure your device appears in Device Management

3. **Check API Permissions**
   - Go to: Cloud → API → API Management
   - Enable "Device Management" APIs
   - Verify your Access ID has proper permissions

4. **Verify Device Linkage**
   - Device must be added to Tuya Smart app first
   - Device must appear in Device Management
   - Region must match between app and project

### ✅ Solution 3: Network Packet Capture

Capture the key from network traffic:

1. Install Wireshark
2. Start capturing on your network interface
3. Filter: `ip.addr == YOUR_DEVICE_IP`
4. Control your lamp from Tuya Smart app
5. Analyze Tuya protocol packets
6. Extract key from encrypted packets

⚠️ Requires network analysis knowledge

### ✅ Solution 4: Extract from Tuya Smart App (Android Root)

1. Root your Android device
2. Install Tuya Smart app and add your lamp
3. Use root file explorer
4. Navigate to: `/data/data/com.tuya.smart/`
5. Find database files (.db)
6. Open with SQLite viewer
7. Find device table, get `localKey` column

⚠️ Requires root access

## Quick Fix Steps

1. **Skip the wizard's cloud API part**
2. **Use web interface instead:**
   - Login to https://iot.tuya.com/
   - Get local_key from Device Management
3. **Update your script:**
   ```python
   # In avant_control.py
   AVANT_KEY = "your_key_from_web_interface"
   ```
4. **Test:**
   ```bash
   python avant_control.py off
   ```

## Why Web Interface Works

- The web interface has different permissions than the API
- It's designed for manual device management
- It doesn't require API service subscriptions
- It's the most reliable method

## Summary

**Best approach:** Use the web interface to get your local_key. It's the simplest and most reliable method, and it bypasses all API permission issues.

Once you have the key, just update `avant_control.py` and you're ready to control your Avant lamp!
