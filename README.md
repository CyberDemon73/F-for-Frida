### README.md

# Frida Server Automation Script

This script automates the installation and management of the Frida server on an Android device via ADB (Android Debug Bridge). It checks if Frida is already installed, handles version compatibility, and installs the Frida server if required. Additionally, it can install the Frida tools on your local machine and ensure they match the version of Frida installed on your device.

---

## Features
- **Device Root Access Check**: Confirms if the connected Android device is rooted before proceeding with Frida installation.
- **Frida Server Installation**: Downloads and installs the Frida server on your Android device based on the specified version.
- **Version Compatibility**: Ensures the installed Frida server version on the Android device matches the Frida version on your local machine.
- **Frida Tools Installation**: Automatically installs or updates `frida-tools` on your local machine to match the Frida version.
- **Custom Path Handling**: Allows the user to specify custom paths for the Frida server binaries.
- **Logging**: Logs important events and actions taken by the script for later review.

---

## Requirements

### Python Dependencies:
1. Python 3.x
2. `requests` - For downloading Frida server binaries.
3. `tqdm` - For displaying download progress.
4. `colorama` - For terminal color formatting.
5. `adb` - Ensure ADB is installed on your system and is accessible via your `PATH`.

You can install the required Python dependencies using pip:

```bash
pip install requests tqdm colorama
```

### System Dependencies:
- ADB (Android Debug Bridge)
- xz-utils (`xz`) - For decompressing `.xz` files. Make sure `xz` is installed on your system:
  - **Debian/Ubuntu**: `sudo apt-get install xz-utils`
  - **macOS (Homebrew)**: `brew install xz`
  - **Windows**: Install via WSL or a third-party package manager like Chocolately.

---

## Usage

### Running the Script:

1. **Ensure Device is Connected and Rooted**:
   - Make sure your Android device is connected via USB and is detected by ADB.
   - Your device must be rooted to install and run the Frida server.

2. **Run the Script**:
   - Open a terminal or command prompt and execute the script as follows:
   ```bash
   python F-for-Frida.py
   ```

3. **Follow the Prompts**:
   - The script will ask for the desired Frida version (e.g., `16.1.17`). If Frida is not installed, it will download, extract, and install it on your Android device.
   - If Frida is already installed, the script will check the version and give you the option to update or leave it unchanged.

4. **Custom Path Option**:
   - The script provides an option to specify a custom path for the Frida server binary on the device, defaulting to `/data/local/tmp`.

### Example:

```bash
Enter the Frida version you want to use or install (e.g., 16.1.17): 16.1.17
Waiting for a device to be connected...
Frida version 16.1.17 is already installed on your machine.
Checking if Frida is running on the device...
Frida server is not found on the device. Proceeding to install...
Downloading Frida server from: https://github.com/frida/frida/releases/download/16.1.17/frida-server-16.1.17-android-arm64.xz
Extracting frida-server-16.1.17-android-arm64.xz...
Frida 16.1.17 installed on the device in /data/local/tmp/frida-server-16.1.17-android-arm64.
Starting Frida server at /data/local/tmp/frida-server-16.1.17-android-arm64 with root privileges...
Frida server started successfully.
```

---

## Key Functions Overview

### `check_root()`
- Verifies if the connected Android device has root access using ADB.

### `download_frida_server(version, os_type, architecture)`
- Downloads the specified Frida server binary from the official Frida GitHub releases.

### `install_frida(version)`
- Installs the specified version of Frida on the local machine using pip.

### `install_frida_on_device(version, os_type, architecture)`
- Installs the specified version of the Frida server on the connected Android device.

### `run_frida_server(frida_server_path)`
- Starts the Frida server on the Android device with root privileges.

---

## Logging

All events, including errors, are logged to a file named `frida_script.log` in the script directory. You can use this log file to review what happened during the execution of the script.

---

## Troubleshooting

1. **No device connected**:
   - Ensure your Android device is connected via USB and is recognized by ADB. You can check this by running:
     ```bash
     adb devices
     ```

2. **Device not rooted**:
   - Ensure your device has root access. The script cannot install or run Frida without root privileges on the device.

3. **Frida server not running**:
   - If you encounter issues starting the Frida server, ensure your device is rooted and that the correct architecture and version of the Frida server has been installed.

---

## License

This project is licensed under the MIT License.

---

### Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request if you have suggestions or improvements.

---
