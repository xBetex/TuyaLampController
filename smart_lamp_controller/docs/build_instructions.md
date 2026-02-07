# Build Instructions for Smart Lamp Controller

## Quick Build (Recommended)

### Option 1: Using the Build Script
1. Open Command Prompt or PowerShell
2. Navigate to the project directory:
   ```cmd
   cd smart_lamp_controller
   ```
3. Run the build script:
   ```cmd
   python build.py
   ```

This will:
- Install all required dependencies
- Build a single executable file
- Create a portable package with launcher

### Option 2: Manual Build
1. Install dependencies:
   ```cmd
   pip install pyinstaller tinytuya pyaudio numpy scipy
   ```
2. Build executable:
   ```cmd
   pyinstaller --name=SmartLampController --windowed --onefile main.py
   ```

## Output Files

After building, you'll find:

### Single Executable
- Location: `dist/SmartLampController.exe`
- Standalone file that can be run anywhere

### Portable Package
- Location: `dist/SmartLampController_Portable/`
- Contains:
  - `SmartLampController.exe` (main executable)
  - `Start_Smart_Lamp_Controller.bat` (easy launcher)
  - `README.md` (documentation)
  - `logs/` folder (for log files)

## Installation Options

### Option 1: Portable (No Installation Required)
1. Copy the entire `SmartLampController_Portable` folder
2. Run `Start_Smart_Lamp_Controller.bat` or `SmartLampController.exe`

### Option 2: Install as Python Package
1. Install from source:
   ```cmd
   pip install -e .
   ```
2. Run from command line:
   ```cmd
   smart-lamp-controller
   ```

## Troubleshooting

### Common Build Issues

#### 1. PyInstaller Not Found
```cmd
pip install pyinstaller
```

#### 2. Audio Dependencies Missing
The build script tries to install audio dependencies, but they may fail on some systems. The app will still work without audio features.

#### 3. Antivirus Warnings
Some antivirus software may flag the executable as suspicious. This is a false positive common to PyInstaller apps.

#### 4. Missing DLL Errors
If you get DLL errors, try:
```cmd
pip install --upgrade pyinstaller
```

### Runtime Issues

#### 1. Device Not Found
- Check your lamp is on the same network
- Verify device configuration in `lamp_config.json`

#### 2. Audio Not Working
- Install audio dependencies: `pip install pyaudio numpy scipy`
- Check microphone permissions

#### 3. Permission Errors
- Run as administrator if needed
- Check firewall settings

## Advanced Build Options

### Custom Icon
Add an icon file to the project and modify `build.py`:
```python
"--icon=your_icon.ico",
```

### Include Additional Files
Modify the build script to include more files:
```python
"--add-data=your_file.txt;.",
```

### Debug Mode
For debugging, build with console:
```python
"--console",  # Show console for debugging
```

## Distribution

### For Personal Use
- Use the portable package
- No installation required

### For Distribution
1. Test the executable on multiple systems
2. Include the README and configuration instructions
3. Consider creating an installer (NSIS, Inno Setup)

## System Requirements

### Minimum
- Windows 7 or later
- Python 3.7+ (for source version)
- Network connection to lamp

### Recommended
- Windows 10 or later
- 4GB RAM
- Microphone (for audio features)

## Support

For issues:
1. Check the troubleshooting section
2. Review the main README.md
3. Check device configuration
4. Test network connectivity
