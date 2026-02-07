#!/usr/bin/env python3
"""
Simple build script for Smart Lamp Controller executable (Python 3.13 preferred)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def _python_exec_override() -> str:
    """Return the Python executable to use for building.

    Priority order:
    - CLI arg --python <path>
    - Env var PYTHON313
    - Current interpreter (sys.executable)
    """
    # Simple CLI parsing
    if "--python" in sys.argv:
        try:
            idx = sys.argv.index("--python")
            return sys.argv[idx + 1]
        except Exception:
            pass
    # Environment override
    env_py = os.environ.get("PYTHON313")
    if env_py:
        return env_py
    return sys.executable


def _check_python_version(py_exec: str) -> None:
    """Warn if not using Python 3.13."""
    try:
        out = subprocess.check_output([py_exec, "-c", "import sys; print(sys.version.split()[0])"], text=True).strip()
        if not out.startswith("3.13"):
            print(f"[Warning] Detected Python {out}. Python 3.13 is recommended for this build.")
            print("          To force Python 3.13 on Windows, you can use the py launcher:")
            print("          py -3.13 -m venv .venv && .\\.venv\\Scripts\\Activate.ps1")
            print("          Then run: python build_simple.py")
    except Exception as e:
        print(f"[Info] Could not verify Python version: {e}")


def install_pyinstaller(py_exec: str) -> bool:
    """Install PyInstaller using the specified Python interpreter"""
    print("Installing PyInstaller (into the selected Python environment)...")
    try:
        # Use a recent PyInstaller (3.13 compatibility is in 6.4+)
        subprocess.check_call([py_exec, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([py_exec, "-m", "pip", "install", "pyinstaller>=6.4"])
        print("PyInstaller installed successfully")
    except subprocess.CalledProcessError:
        print("Failed to install PyInstaller")
        return False
    return True


def build_basic_executable(py_exec: str) -> bool:
    """Build executable without optional audio dependencies"""
    print("Building basic executable...")

    # Run PyInstaller via the chosen interpreter (avoids PATH issues)
    cmd = [
        py_exec,
        "-m",
        "PyInstaller",
        "--name=SmartLampController",
        "--windowed",  # No console window
        "--onefile",   # Single executable
        "--add-data=README.md;.",  # Include README (Windows uses ';')
        # Hidden imports are often unnecessary; include minimal set only if needed
        "main.py",
    ]

    try:
        subprocess.check_call(cmd)
        print("Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False


def create_simple_package():
    """Create a simple package"""
    dist_dir = Path.cwd() / "dist"
    portable_dir = dist_dir / "SmartLampController_Simple"
    
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # Copy executable
    exe_path = dist_dir / "SmartLampController.exe"
    if exe_path.exists():
        shutil.copy2(exe_path, portable_dir / "SmartLampController.exe")
        print(f"Executable copied to: {portable_dir / 'SmartLampController.exe'}")
    
    # Copy essential files
    essential_files = ["README.md", "requirements.txt", "build_instructions.md"]
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, portable_dir / file)
    
    # Create directories
    (portable_dir / "logs").mkdir(exist_ok=True)
    
    # Create a simple launcher script
    launcher_content = """@echo off
title Smart Lamp Controller
echo Starting Smart Lamp Controller...
echo.
echo Note: Audio features require additional dependencies
echo See requirements.txt for more information
echo.
SmartLampController.exe
if errorlevel 1 (
    echo.
    echo An error occurred. Check logs folder for details.
    pause
)
"""
    with open(portable_dir / "Start_Smart_Lamp_Controller.bat", "w") as f:
        f.write(launcher_content)
    
    # Create installation instructions
    install_content = """# Smart Lamp Controller - Installation

## Quick Start
1. Double-click "Start_Smart_Lamp_Controller.bat" to run the application
2. Or run "SmartLampController.exe" directly

## Audio Features (Optional)
To enable audio synchronization features:
1. Install Python 3.7+ from python.org
2. Run: pip install pyaudio numpy scipy
3. Restart the application

## Configuration
The application will create a configuration file (lamp_config.json) on first run.
Edit this file to configure your lamp device details.

## Troubleshooting
- If the app doesn't start, check the logs folder
- Ensure your lamp is connected to the same network
- Verify device configuration in lamp_config.json

## Support
See README.md for detailed documentation
"""
    
    with open(portable_dir / "INSTALLATION.txt", "w") as f:
        f.write(install_content)
    
    print(f"Simple package created in: {portable_dir}")
    return portable_dir

def main():
    """Main build process"""
    print("Smart Lamp Controller - Simple Build Script (Python 3.13)")
    print("=" * 55)

    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("Error: main.py not found. Please run this script from the smart_lamp_controller directory.")
        return 1

    # Choose Python interpreter
    py_exec = _python_exec_override()
    _check_python_version(py_exec)

    # Install PyInstaller
    if not install_pyinstaller(py_exec):
        print("Please install PyInstaller manually in your Python 3.13 environment: pip install pyinstaller")
        return 1

    # Build executable
    if not build_basic_executable(py_exec):
        return 1
    
    # Create package
    package_dir = create_simple_package()
    
    print("\n" + "=" * 45)
    print("BUILD COMPLETED SUCCESSFULLY!")
    print("=" * 45)
    print(f"Executable: {package_dir / 'SmartLampController.exe'}")
    print(f"Launcher: {package_dir / 'Start_Smart_Lamp_Controller.bat'}")
    print(f"Instructions: {package_dir / 'INSTALLATION.txt'}")
    print("\nThe application is ready to use!")
    print("Note: Audio features require additional Python dependencies.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
