# Smart Lamp Pairing Guide

This guide explains how to pair your Tuya smart lamp directly with your PC without using the mobile app.

## Understanding Tuya Device Pairing

Tuya devices create a temporary WiFi hotspot when in pairing mode. Your PC needs to connect to this temporary network to complete the initial pairing process.

## Step-by-Step Pairing Process

### 1. Put Lamp in Pairing Mode
1. **Power cycle the lamp 5+ times** quickly (on/off repeatedly)
2. The lamp should start **blinking rapidly** to indicate pairing mode
3. The lamp will now broadcast a temporary WiFi network

### 2. Connect PC to Lamp's Temporary Network
1. Open your computer's WiFi settings
2. Look for a network named something like:
   - `SmartLife-XXXX`
   - `Tuya-XXXX` 
   - `Lamp-XXXX`
   - Similar pattern with 4 digits
3. **Connect to this network** (no password usually required)

### 3. Run the Pairing Script
Once connected to the lamp's temporary network:

```bash
python scripts/pair_lamp.py
```

The script will:
1. Scan for devices on the current network
2. If found, let you select the lamp
3. Test the connection
4. Save the configuration

### 4. Manual Pairing (If Auto-Discovery Fails)

If automatic discovery doesn't work, you can pair manually:

1. Run the pairing script
2. When no devices are found, choose manual pairing
3. Enter the lamp's IP address (usually `192.168.4.1`)
4. Leave device ID empty for auto-discovery
5. Use default version (3.5)

### 5. Return to Normal Network

After successful pairing:
1. **Disconnect** from the lamp's temporary WiFi
2. **Reconnect** to your regular WiFi network
3. The lamp will now be accessible through your main network

## Common Issues and Solutions

### No Devices Found
- **Ensure lamp is in pairing mode** (blinking rapidly)
- **Connect to the lamp's temporary WiFi** first
- **Disable VPN** if active
- **Temporarily disable firewall** for pairing

### Connection Failed
- **Try again** - pairing can be finicky
- **Restart the pairing process** (power cycle lamp again)
- **Check IP address** if using manual pairing (try `192.168.4.1`)

### Can't Find Temporary WiFi
- **Power cycle lamp more times** (5-10 times)
- **Wait 30 seconds** after pairing mode starts
- **Move closer** to the lamp
- **Try different timing** for power cycling

## After Pairing

Once paired successfully:
1. The lamp will be configured in `lamp_config.json`
2. You can run the main application: `python main.py`
3. The lamp will work through your regular WiFi network

## Technical Details

- **Temporary Network**: Lamp creates AP mode WiFi (usually 192.168.4.x)
- **Pairing Protocol**: Tuya's cloud-free pairing over local network
- **Configuration**: Device ID, local key, and IP are saved locally
- **Network Switch**: After pairing, lamp joins your main WiFi

## Troubleshooting Commands

If you're still having issues, try these diagnostic steps:

```bash
# Check if you can reach the lamp (when connected to its network)
ping 192.168.4.1

# Scan network devices (Windows)
netstat -an | findstr 192.168

# Check WiFi networks (Windows)
netsh wlan show networks
```

## Alternative Methods

If the script method doesn't work:
1. **Use the official Tuya Smart app** to pair first
2. **Extract credentials** from the app (advanced)
3. **Use Tuya IoT Platform** for developer access

The pairing script is designed to be the simplest method for direct PC pairing without mobile apps.
