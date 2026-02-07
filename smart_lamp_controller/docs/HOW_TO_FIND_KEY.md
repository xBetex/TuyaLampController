# 🔑 How to Find Your Local Key - Step by Step

## You're Almost There! ✅

Your device "Lâmpada NEO 10W RGB" is added and you have all the function codes!

## Finding the Local Key

### Method 1: Debug Device Page (Easiest)

1. **In the device table**, click the blue **"Debug Device"** link in the "Operation" column
2. This opens the device debug/details page
3. **Look for these fields:**
   - "Local Key"
   - "Device Secret" 
   - "local_key"
   - "localKey"
4. **Copy the value** (usually 16 hex characters like `a1b2c3d4e5f6g7h8`)

### Method 2: Device Details Page

1. **Click on your device name** or **Device ID** in the table
2. This opens the full device details page
3. **Look in these sections:**
   - Device Information
   - Device Configuration
   - Security Settings
   - Device Credentials
4. **Find "Local Key"** and copy it

### Method 3: API Explorer (If web interface doesn't show it)

1. Go to: **Cloud → API Explorer**
2. Select: **Device Management → Query Device Details**
3. Enter Device ID: `YOUR_DEVICE_ID`
4. Click "Send Request"
5. Look for `local_key` in the JSON response

## What the Key Looks Like

- **Length:** 16 characters (sometimes 32)
- **Format:** Hexadecimal (0-9, a-f)
- **Example:** `a1b2c3d4e5f6g7h8` or `0123456789abcdef`
- **Case:** Usually lowercase, sometimes uppercase

## Once You Have the Key

1. **Open `avant_control_with_functions.py`**
2. **Update this line:**
   ```python
   LOCAL_KEY = "your_copied_key_here"
   ```
3. **Test it:**
   ```bash
   python avant_control_with_functions.py status
   python avant_control_with_functions.py on
   python avant_control_with_functions.py off
   ```

## Your Device Functions

I've created a control script that uses ALL your device functions:

- ✅ Power on/off (`switch_led`)
- ✅ Brightness control (`bright_value_v2`)
- ✅ Color temperature (`temp_value_v2`)
- ✅ RGB color (`colour_data_v2`)
- ✅ White mode (`work_mode`)
- ✅ Scene modes (`scene_data_v2`)
- ✅ And more!

## If You Still Can't Find It

Some newer devices don't expose local_key in the web interface. Try:

1. **Network packet capture** (Wireshark)
2. **Extract from Tuya Smart app** (if rooted)
3. **Contact Tuya support** (they might provide it)

But first, make sure you've checked:
- ✅ Debug Device page
- ✅ Device Details page  
- ✅ All tabs/sections on device page
- ✅ API Explorer response

The key is definitely there somewhere - it's just a matter of finding the right page/section!
