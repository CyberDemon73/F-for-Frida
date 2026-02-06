<p align="center">
  <img src="https://frida.re/img/logotype.svg" alt="Frida Logo" width="200"/>
</p>

<h1 align="center">F-for-Frida</h1>

<p align="center">
  <strong>🔧 Automated Frida Server Management for Android Devices</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#commands">Commands</a> •
  <a href="#multi-device">Multi-Device</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg" alt="Platform"/>
  <img src="https://img.shields.io/badge/frida-supported-orange.svg" alt="Frida"/>
</p>

---

## 📖 Overview

**F-for-Frida** is a powerful Python tool that automates the entire lifecycle of managing Frida server on Android devices. Whether you're doing security research, mobile app testing, or reverse engineering, this tool simplifies the tedious process of downloading, installing, and managing Frida server instances.

### Why F-for-Frida?

- 🚀 **One-command setup** - Get Frida running in seconds
- 📱 **Multi-device support** - Manage multiple Android devices simultaneously
- 🔄 **Auto-architecture detection** - Automatically detects ARM64, ARM, x86, or x86_64
- 📦 **Version management** - Install any Frida version with ease
- 🎨 **Beautiful CLI** - Rich terminal interface with colors and progress indicators

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Device Detection** | Auto-detect connected devices and their authorization status |
| **Root Verification** | Validate root access before Frida operations |
| **Architecture Detection** | Auto-detect CPU architecture for correct binary download |
| **Version Management** | Install specific or latest Frida server versions |
| **Process Management** | Start, stop, restart Frida server with PID tracking |
| **Multi-Device Support** | Target specific devices in multi-device setups |
| **Interactive Mode** | User-friendly menu-driven interface |
| **Logging** | Comprehensive logging for debugging |

---

## 📋 Prerequisites

Before using F-for-Frida, ensure you have:

1. **Python 3.8+** installed on your system
2. **ADB (Android Debug Bridge)** installed and in your PATH
   - Windows: Install via [Android SDK Platform Tools](https://developer.android.com/studio/releases/platform-tools)
   - Linux: `sudo apt install adb`
   - macOS: `brew install android-platform-tools`
3. **XZ Utils** for extracting Frida server archives
   - Windows: Install via `winget install xz` or download from [tukaani.org](https://tukaani.org/xz/)
   - Linux: `sudo apt install xz-utils`
   - macOS: `brew install xz`
4. **Rooted Android device** with USB debugging enabled

---

## 🚀 Installation

### Option 1: Install from Source (Recommended)

```bash
# Clone the repository
git clone https://github.com/CyberDemon73/F-for-Frida.git
cd F-for-Frida

# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Install the package
pip install -e .
```

### Option 2: Install Dependencies Only

```bash
# Clone and install dependencies
git clone https://github.com/CyberDemon73/F-for-Frida.git
cd F-for-Frida
pip install -r requirements.txt

# Run directly
python main.py
```

---

## 💻 Usage

### Quick Start

```bash
# List connected devices
f4f devices

# Install latest Frida server
f4f install --latest

# Start Frida server
f4f start

# Check status
f4f status
```

### Interactive Mode

For a guided experience, use interactive mode:

```bash
f4f interactive
```

This provides a menu-driven interface for all operations.

---

## 📚 Commands

### `devices` - List Connected Devices

```bash
# Basic device list
f4f devices

# Detailed info (architecture, root status, Android version)
f4f devices --detailed
```

**Output:**
```
┌──────────────────────────────────────────────────┐
│                Connected Devices                  │
├──────────────┬──────────┬────────────────────────┤
│ Serial       │ Status   │ Model                  │
├──────────────┼──────────┼────────────────────────┤
│ RF8M33XXXXX  │ device   │ SM-G998B               │
│ emulator-5554│ device   │ Android SDK built...   │
└──────────────┴──────────┴────────────────────────┘
```

### `status` - Check Frida Server Status

```bash
# Check on default/only device
f4f status

# Check specific device
f4f status -s RF8M33XXXXX
```

### `install` - Install Frida Server

```bash
# Install latest version
f4f install --latest

# Install specific version
f4f install 16.1.17

# Force reinstall
f4f install 16.1.17 --force

# Install on specific device
f4f install --latest -s RF8M33XXXXX
```

### `start` - Start Frida Server

```bash
# Start server
f4f start

# Start specific version
f4f start 16.1.17

# Start on specific device
f4f start -s RF8M33XXXXX
```

### `stop` - Stop Frida Server

```bash
# Stop all instances
f4f stop

# Stop specific PID
f4f stop --pid 12345

# Stop on specific device
f4f stop -s RF8M33XXXXX
```

### `restart` - Restart Frida Server

```bash
f4f restart
```

### `versions` - List Available Versions

```bash
# Show 10 latest versions
f4f versions

# Show more versions
f4f versions --limit 20
```

---

## 📱 Multi-Device Support

F-for-Frida fully supports multiple connected devices. Use the `-s` or `--device` flag to target a specific device:

```bash
# List all devices first
f4f devices

# Target specific device for any command
f4f status -s RF8M33XXXXX
f4f install --latest -s emulator-5554
f4f start -s RF8M33XXXXX
```

If only one device is connected, it's automatically selected. If multiple devices are connected without specifying one, you'll be prompted to select.

---

## 🏗️ Project Structure

```
F-for-Frida/
├── f_for_frida/              # Main package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # CLI interface (Click + Rich)
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── adb.py            # ADB client wrapper
│   │   ├── device.py         # Device management
│   │   └── frida_manager.py  # Frida server management
│   └── utils/                # Utilities
│       ├── __init__.py
│       ├── downloader.py     # Download utilities
│       └── logger.py         # Logging configuration
├── main.py                   # Entry point
├── setup.py                  # Package setup
├── requirements.txt          # Dependencies
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## 🔧 Configuration

### Logging

Enable verbose logging with the `--verbose` flag:

```bash
f4f --verbose status
```

Save logs to file:

```bash
f4f --log-file frida.log install --latest
```

### Default Frida Port

Frida server uses port **27042** by default. This is checked when verifying server status.

---

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><strong>❌ "No device connected"</strong></summary>

1. Ensure USB debugging is enabled on your device
2. Check USB cable connection
3. Run `adb devices` to verify ADB sees your device
4. Authorize the computer on your device if prompted
</details>

<details>
<summary><strong>❌ "Device is not rooted"</strong></summary>

Frida requires root access. Options:
1. Root your device using Magisk or similar
2. Use an emulator with root access
3. For non-root, use `frida-gadget` instead (manual integration)
</details>

<details>
<summary><strong>❌ "'xz' command not found"</strong></summary>

Install XZ Utils:
- **Windows**: `winget install xz` or download from [tukaani.org](https://tukaani.org/xz/)
- **Linux**: `sudo apt install xz-utils`
- **macOS**: `brew install xz`
</details>

<details>
<summary><strong>❌ "Frida server fails to start"</strong></summary>

1. Check SELinux: `adb shell su -c "setenforce 0"`
2. Verify binary permissions: `adb shell ls -la /data/local/tmp/frida-server*`
3. Check logs: `adb logcat | grep frida`
4. Try reinstalling: `f4f install --latest --force`
</details>

<details>
<summary><strong>❌ "Download failed"</strong></summary>

1. Check internet connection
2. Verify the Frida version exists: `f4f versions`
3. GitHub may be rate-limiting - wait a few minutes
</details>

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/F-for-Frida.git
cd F-for-Frida

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black f_for_frida/

# Lint
flake8 f_for_frida/
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Frida](https://frida.re/) - The amazing dynamic instrumentation toolkit
- [Click](https://click.palletsprojects.com/) - Beautiful CLI library
- [Rich](https://rich.readthedocs.io/) - Rich text formatting for terminals

---

## 📬 Contact

- **Author**: Mohamed Hisham Sharaf
- **GitHub**: [@CyberDemon73](https://github.com/CyberDemon73)

---

<p align="center">
  <sub>Made with ❤️ for the security research community</sub>
</p>
