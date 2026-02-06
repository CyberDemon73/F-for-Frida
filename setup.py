#!/usr/bin/env python3
"""
Setup script for F-for-Frida
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read version from package
version = "2.0.0"

setup(
    name="f-for-frida",
    version=version,
    author="Mohamed Hisham Sharaf",
    author_email="",
    description="Automated Frida Server Management for Android Devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CyberDemon73/F-for-Frida",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Testing",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "tqdm>=4.65.0",
        "colorama>=0.4.6",
        "click>=8.1.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "f4f=f_for_frida.cli:main",
            "f-for-frida=f_for_frida.cli:main",
        ],
    },
    keywords=[
        "frida",
        "android",
        "security",
        "reverse-engineering",
        "mobile",
        "adb",
        "debugging",
    ],
    project_urls={
        "Bug Reports": "https://github.com/CyberDemon73/F-for-Frida/issues",
        "Source": "https://github.com/CyberDemon73/F-for-Frida",
    },
)
