# How to Find the Local Key in Tuya IoT Platform

## You've Added the Device! ✅

Great! I can see your device "Lâmpada NEO 10W RGB" is now in your Tuya IoT Platform.

## Where to Find the Local Key

### Step 1: Click on "Debug Device"

In the device table you showed, there's an "Operation" column with "Debug Device" (blue link).

1. **Click on "Debug Device"** - This opens the device debug/details page

### Step 2: Look for Local Key

On the device details/debug page, look for:

- **"Local Key"** field
- **"Device Secret"** field  
- **"local_key"** field
- **"localKey"** field

It's usually in one of these sections:
- Device Information
- Device Details
- Device Configuration
- Security Settings

### Step 3: Alternative - Device Details Page

If "Debug Device" doesn't show it, try:

1. Click on the **Device ID** or **Device Name** in the table
2. This opens the full device details page
3. Look for "Local Key" in the device information section

### Step 4: What the Key Looks Like

The local_key will be:
- **16 hexadecimal characters** (0-9, a-f)
- Example: `a1b2c3d4e5f6g7h8`
- Sometimes it might be 32 characters (less common)

### Step 5: Copy the Key

Once you find it:
1. Copy the entire key value
2. Update `avant_control_with_functions.py`:
   ```python
   LOCAL_KEY = "your_copied_key_here"
   ```

## If You Still Can't Find It

Some devices don't expose the local_key via the web interface. In that case:

1. **Check API Explorer**:
   - Go to: Cloud → API Explorer
   - Select: Device Management → Query Device Details
   - Enter your Device ID: `YOUR_DEVICE_ID`
   - Look for `local_key` in the response

2. **Use Network Capture**:
   - Install Wireshark
   - Capture traffic while controlling from Tuya Smart app
   - Extract key from packets

3. **Extract from App** (if rooted):
   - Android: `/data/data/com.tuya.smart/` database
   - Look for `localKey` column

## Your Device Functions

I've created `avant_control_with_functions.py` that uses all the function codes you found:

- `switch_led` - Power on/off
- `work_mode` - Mode selection
- `bright_value_v2` - Brightness control
- `temp_value_v2` - Color temperature
- `colour_data_v2` - RGB color control
- `scene_data_v2` - Scene modes
- And more!

Once you have the key, you can control all these features!
