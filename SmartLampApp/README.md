# Smart Lamp Controller App

This is a native Android application built with Kotlin and Jetpack Compose to control the Smart Lamp via its local REST API.

## Features
- **Connect/Status**: Manage connection to the lamp (Base URL persistence).
- **White Light**: Control brightness and temperature (warm/cool).
- **Static Color**: RGB sliders to set specific colors.
- **Effects**: Start and stop the Rainbow effect with speed control.

## Prerequisites
- Android Studio Hedgehog (2023.1.1) or newer recommended.
- Android SDK API 34.
- Java 17 (Gradle uses this).

## Setup & Build
1.  **Open in Android Studio**:
    - Open Android Studio.
    - Select **Open** and navigate to this `SmartLampApp` directory.
    - Android Studio should automatically sync Gradle and generate the necessary wrapper files if they are missing.

2.  **Verify Configuration**:
    - The app is configured to allow cleartext traffic (HTTP) to `192.168.15.7`. If your lamp is on a different IP, you can change it in the app's Connect screen.
    - If you are running the server on your PC and testing on the Android Emulator, use `http://10.0.2.2:8765`.

3.  **Run the App**:
    - Select the `app` configuration.
    - Choose a connected device or an emulator.
    - Click **Run**.

## Build APK
To build a release APK:
1.  Go to **Build > Generate Signed Bundle / APK**.
2.  Choose **APK**.
3.  Create a new keystore or choose an existing one.
4.  Select `release` build variant.
5.  The APK will be generated in `app/release/`.

## Troubleshooting
- **Connection Failed**: Ensure your phone is on the same Wi-Fi network as the computer/lamp server.
- **Cleartext Error**: If you change the IP to something not covered in `network_security_config.xml`, you might get a cleartext error. The config currently allows `192.168.15.7` and `10.0.2.2`. For other IPs, you may need to update `app/src/main/res/xml/network_security_config.xml`.

## Project Structure
- `ui/`: Compose UI screens and logic.
- `network/`: Retrofit API client.
- `data/`: DataStore for settings (persisting the API URL).
- `model/`: Data classes matching the REST API.
