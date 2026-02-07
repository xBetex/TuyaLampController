#!/usr/bin/env python3
"""
Build script for Smart Lamp Controller executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_requirements():
    """Install required packages for building"""
    print("Installing build requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "tinytuya"])
    
    # Optional audio dependencies
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyaudio", "numpy", "scipy"])
        print("Audio dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Warning: Audio dependencies could not be installed. Audio features will be disabled.")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=SmartLampController",
        "--windowed",  # No console window
        "--onefile",   # Single executable
        "--add-data=README.md;.",  # Include README
        "--icon=NONE",  # You can add an icon file here
        "--hidden-import=tinytuya",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.colorchooser",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=queue",
        "--hidden-import=threading",
        "--hidden-import=time",
        "--hidden-import=colorsys",
        "--hidden-import=json",
        "--hidden-import=logging",
        "--hidden-import=pathlib",
        "--hidden-import=numpy",  # Optional
        "--hidden-import=scipy",  # Optional
        "--hidden-import=pyaudio",  # Optional
        "main.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        print(f"Executable created in: {Path.cwd() / 'dist' / 'SmartLampController.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False
    
    return True

def create_portable_package():
    """Create a portable package with executable"""
    dist_dir = Path.cwd() / "dist"
    portable_dir = dist_dir / "SmartLampController_Portable"
    
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # Copy executable
    exe_path = dist_dir / "SmartLampController.exe"
    if exe_path.exists():
        shutil.copy2(exe_path, portable_dir / "SmartLampController.exe")
    
    # Copy essential files
    essential_files = ["README.md", "requirements.txt"]
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, portable_dir / file)
    
    # Create directories
    (portable_dir / "logs").mkdir(exist_ok=True)
    
    # Create a simple launcher script
    launcher_content = """@echo off
echo Starting Smart Lamp Controller...
echo.
SmartLampController.exe
pause
"""
    with open(portable_dir / "Start_Smart_Lamp_Controller.bat", "w") as f:
        f.write(launcher_content)
    
    print(f"Portable package created in: {portable_dir}")

def main():
    """Main build process"""
    print("Smart Lamp Controller - Build Script")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("Error: main.py not found. Please run this script from the project directory.")
        return 1
    
    # Install requirements
    try:
        install_requirements()
    except subprocess.CalledProcessError:
        print("Failed to install requirements. Please install them manually:")
        print("pip install pyinstaller tinytuya pyaudio numpy scipy")
        return 1
    
    # Build executable
    if not build_executable():
        return 1
    
    # Create portable package
    create_portable_package()
    
    print("\nBuild process completed!")
    print("You can find the executable in the 'dist' folder.")
    print("A portable package is also available in 'dist/SmartLampController_Portable'")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
