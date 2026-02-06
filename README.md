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
  <a href="#scripts">Scripts</a> •
  <a href="#wireless">Wireless</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg" alt="Platform"/>
  <img src="https://img.shields.io/badge/frida-supported-orange.svg" alt="Frida"/>
  <img src="https://github.com/CyberDemon73/F-for-Frida/actions/workflows/ci.yml/badge.svg" alt="CI"/>
</p>

---

## 📖 Overview

**F-for-Frida** is a powerful Python tool that automates the entire lifecycle of managing Frida server on Android devices. Whether you're doing security research, mobile app testing, or reverse engineering, this tool simplifies the tedious process of downloading, installing, and managing Frida server instances.

### Why F-for-Frida?

- 🚀 **One-command setup** - Get Frida running in seconds
- 📱 **Multi-device support** - Manage multiple Android devices simultaneously
- 🌐 **Wireless ADB** - Connect to devices over WiFi
- 📜 **Built-in scripts** - SSL pinning bypass, root detection bypass, and more
- 🔄 **Auto-architecture detection** - Automatically detects ARM64, ARM, x86, or x86_64
- 📦 **Version management** - Install any Frida version with ease
- 🩺 **Health diagnostics** - Built-in doctor command for troubleshooting
- 🎨 **Beautiful CLI** - Rich terminal interface with colors and progress indicators

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Device Detection** | Auto-detect connected devices and their authorization status |
| **Wireless ADB** | Connect, pair, and manage devices over WiFi |
| **Root Verification** | Validate root access before Frida operations |
| **Architecture Detection** | Auto-detect CPU architecture for correct binary download |
| **Version Management** | Install specific or latest Frida server versions |
| **Built-in Scripts** | SSL bypass, root bypass, anti-debug, crypto logger, and more |
| **App Hooking** | Simplified interface for hooking applications |
| **Process Management** | Start, stop, restart Frida server with PID tracking |
| **Health Diagnostics** | Doctor command to diagnose common issues |
| **Configuration** | YAML/JSON config files with environment variable support |

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
# Check system health
f4f doctor

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

---

## 📚 Commands

### Device Management

```bash
# List all devices
f4f devices

# Detailed device info
f4f devices --detailed

# Check Frida status
f4f status -s DEVICE_SERIAL
```

### Wireless ADB

```bash
# Setup wireless on USB-connected device
f4f wireless setup

# Connect to device over WiFi
f4f wireless connect 192.168.1.100

# Pair with Android 11+ device
f4f wireless pair 192.168.1.100:37123 123456

# Disconnect
f4f wireless disconnect
```

### Frida Server Management

```bash
# Install latest version
f4f install --latest

# Install specific version
f4f install 16.1.17

# Start server
f4f start

# Stop server
f4f stop

# Restart server
f4f restart

# List available versions
f4f versions
```

### Built-in Scripts

```bash
# List available scripts
f4f scripts list

# Show script content
f4f scripts show ssl-pinning-bypass

# Export script to file
f4f scripts export ssl-pinning-bypass -o bypass.js
```

Available scripts:
- `ssl-pinning-bypass` - Bypass SSL certificate pinning
- `root-detection-bypass` - Bypass root detection
- `anti-debug-bypass` - Bypass anti-debugging techniques
- `method-tracer` - Trace method calls
- `crypto-logger` - Log cryptographic operations
- `http-logger` - Log HTTP requests

### Application Hooking

```bash
# List installed apps
f4f hook apps

# List running apps
f4f hook apps --running

# Hook with bypass scripts
f4f hook run com.example.app --bypass ssl --bypass root

# Hook with spawn mode
f4f hook run com.example.app --spawn --script ssl-pinning-bypass

# Start/stop apps
f4f hook start com.example.app
f4f hook kill com.example.app
```

### Health Diagnostics

```bash
# Run all health checks
f4f doctor
```

### Configuration

```bash
# Show current config
f4f config show

# Set a value
f4f config set default_device ABC123

# Initialize config file
f4f config init
```

---

## 📜 Built-in Scripts

F-for-Frida includes several pre-built Frida scripts for common security testing tasks:

| Script | Category | Description |
|--------|----------|-------------|
| `ssl-pinning-bypass` | Network | Bypass SSL certificate pinning (OkHttp, TrustManager, etc.) |
| `root-detection-bypass` | Security | Bypass common root detection mechanisms |
| `anti-debug-bypass` | Security | Bypass anti-debugging techniques |
| `method-tracer` | Analysis | Trace method calls with arguments and return values |
| `crypto-logger` | Crypto | Log cryptographic operations (AES, RSA, hashing) |
| `http-logger` | Network | Log HTTP/HTTPS requests and responses |

### Using Scripts

```bash
# Quick bypass setup
f4f hook run com.target.app --bypass ssl --bypass root --spawn

# Use specific script
f4f hook run com.target.app --script crypto-logger

# Export and customize
f4f scripts export ssl-pinning-bypass -o my_bypass.js
# Edit my_bypass.js as needed
frida -U -f com.target.app -l my_bypass.js
```

---

## 🌐 Wireless ADB Support

F-for-Frida supports wireless ADB connections for untethered testing:

### Quick Setup (USB → WiFi)

```bash
# With device connected via USB
f4f wireless setup

# Output: Wireless setup complete! Device available at 192.168.1.100:5555
```

### Android 11+ Wireless Debugging

```bash
# Enable Wireless debugging on device
# Get pairing code from Developer Options

f4f wireless pair 192.168.1.100:37123 123456
f4f wireless connect 192.168.1.100:5555
```

### Managing Wireless Devices

```bash
# List wireless devices
f4f wireless list

# Disconnect specific device
f4f wireless disconnect 192.168.1.100:5555

# Disconnect all
f4f wireless disconnect
```

---

## ⚙️ Configuration

F-for-Frida supports configuration via files or environment variables.

### Config File

Create `~/.f4f/config.yaml`:

```yaml
# Default device to use
default_device: ABC123

# Default Frida version
default_version: "16.1.17"

# Auto-start server after install
auto_start: true

# Frida server port
frida_port: 27042

# Wireless settings
wireless_port: 5555
saved_wireless_devices:
  - "192.168.1.100:5555"

# Logging
verbose: false
log_file: ~/.f4f/frida.log
```

### Environment Variables

```bash
export F4F_DEFAULT_DEVICE=ABC123
export F4F_DEFAULT_VERSION=16.1.17
export F4F_VERBOSE=true
export F4F_FRIDA_PORT=27042
```

---

## 🏗️ Project Structure

```
F-for-Frida/
├── f_for_frida/              # Main package
│   ├── __init__.py           # Package initialization
│   ├── cli.py                # CLI interface (Click + Rich)
│   ├── core/                 # Core functionality
│   │   ├── adb.py            # ADB client wrapper
│   │   ├── device.py         # Device management
│   │   ├── frida_manager.py  # Frida server management
│   │   ├── wireless.py       # Wireless ADB support
│   │   ├── scripts.py        # Frida scripts management
│   │   ├── doctor.py         # Health diagnostics
│   │   └── hooker.py         # App hooking helpers
│   └── utils/                # Utilities
│       ├── config.py         # Configuration management
│       ├── downloader.py     # Download utilities
│       └── logger.py         # Logging configuration
├── tests/                    # Unit tests
├── .github/                  # GitHub Actions CI/CD
├── main.py                   # Entry point
├── setup.py                  # Package setup
├── pyproject.toml            # Modern Python packaging
├── requirements.txt          # Dependencies
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## 🩺 Troubleshooting

### Quick Diagnostics

```bash
f4f doctor
```

This checks:
- Python version
- ADB installation
- XZ Utils
- Device connection
- Root access
- SELinux status
- Frida server status
- Frida client installation

### Common Issues

<details>
<summary><strong>❌ "No device connected"</strong></summary>

1. Ensure USB debugging is enabled
2. Check USB cable
3. Run `adb devices` to verify
4. Authorize on device if prompted
</details>

<details>
<summary><strong>❌ "Device is not rooted"</strong></summary>

Root your device with Magisk or use a rooted emulator.
</details>

<details>
<summary><strong>❌ "'xz' command not found"</strong></summary>

- Windows: `winget install xz`
- Linux: `sudo apt install xz-utils`
- macOS: `brew install xz`
</details>

<details>
<summary><strong>❌ "Frida server fails to start"</strong></summary>

1. Check SELinux: `adb shell su -c "setenforce 0"`
2. Verify permissions: `adb shell chmod 755 /data/local/tmp/frida-server*`
3. Check logs: `adb logcat | grep frida`
4. Reinstall: `f4f install --latest --force`
</details>

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=f_for_frida

# Format code
black f_for_frida/

# Lint
flake8 f_for_frida/

# Type check
mypy f_for_frida/
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. **Fork** the repository
2. **Create** a feature branch
3. **Commit** your changes
4. **Push** to the branch
5. **Open** a Pull Request

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
