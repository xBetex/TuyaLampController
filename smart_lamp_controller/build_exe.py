#!/usr/bin/env python3
"""
Build script for Smart Lamp Controller executable
"""

import os
import subprocess
import sys

def build_executable():
    """Build the executable using PyInstaller"""
    
    # Clean previous builds
    print("Cleaning previous builds...")
    subprocess.run([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm"], 
                   capture_output=True)
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=SmartLampController",
        "--onefile",  # Create single executable
        "--windowed",  # Change to --console for debugging
        "--add-data=lamp_config.json;.",
        "--add-data=README_ORGANIZATION.md;.",
        "--add-data=src;src",
        "--add-data=core;core", 
        "--add-data=utils;utils",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.colorchooser",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tinytuya",
        "--hidden-import=pyaudio",
        "--hidden-import=numpy",
        "--hidden-import=scipy",
        "--hidden-import=colorsys",
        "--hidden-import=threading",
        "--hidden-import=logging",
        "--hidden-import=json",
        "--hidden-import=pathlib",
        "--hidden-import=typing",
        "--hidden-import=socket",
        "--hidden-import=http.server",
        "--hidden-import=urllib.parse",
        "--hidden-import=time",
        "--hidden-import=sys",
        "--hidden-import=os",
        "--hidden-import=queue",
        "--hidden-import=asyncio",
        "--hidden-import=requests",
        "main.py"
    ]
    
    print("Building executable...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Build successful!")
        print(f"Executable created at: {os.path.abspath('dist/SmartLampController.exe')}")
    else:
        print("Build failed!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    build_executable()
