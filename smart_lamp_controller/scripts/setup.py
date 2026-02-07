#!/usr/bin/env python3
"""
Setup script for Smart Lamp Controller
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="smart-lamp-controller",
    version="2.0.0",
    author="Smart Lamp Controller Team",
    author_email="",
    description="A modular and feature-rich application for controlling Tuya-based RGB smart lamps",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/smart-lamp-controller",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "audio": ["pyaudio>=0.2.11", "numpy>=1.21.0", "scipy>=1.7.0"],
        "dev": ["pytest>=6.0.0", "pytest-asyncio>=0.18.0"],
    },
    entry_points={
        "console_scripts": [
            "smart-lamp-controller=improved_lamp_controller:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json"],
    },
)
