# F-For-Frida

**F-For-Frida** is a Python script that automates the process of managing and interacting with the Frida server on an Android device. It simplifies starting, stopping, and monitoring the Frida server through an ADB (Android Debug Bridge) connection, ensuring that Frida runs with the appropriate permissions on the connected device. 

The script also provides features to check if the device is rooted, verify the correct architecture, and handle different Frida versions.

## Features

- **Device Connection Detection**: Automatically checks if an Android device is connected and authorized for ADB communication.
- **Root Access Verification**: Confirms if the connected device has root privileges (required for running Frida).
- **Frida Server Management**:
  - **Start/Stop Frida Server**: Start and stop the Frida server on the device.
  - **PID Management**: Retrieve and display PIDs for running Frida server instances.
  - **Architecture Detection**: Automatically detects the architecture of the connected device and installs the correct version of the Frida server.
- **Frida Server Version Management**: Install or use specific versions of the Frida server based on user input.
- **Real-Time Monitoring**: Monitors the Frida server's status and verifies if it is running as expected.

## Prerequisites

1. **ADB (Android Debug Bridge)** installed and configured on your machine.
2. **Python 3.6+** installed.
3. **Frida-tools** installed on your local machine:
   ```bash
   pip install frida-tools
   ```
4. An **Android device** with root access and USB debugging enabled.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/CyberDemon73/F-For-Frida.git
   cd F-For-Frida
   ```

2. **Install Python Dependencies**:
   Install the necessary Python libraries by running:
   ```bash
   pip install -r requirements.txt
   ```
   Required dependencies:
   - `tqdm`
   - `colorama`
   - `requests`

3. **Connect Your Android Device**:
   - Enable **USB Debugging** on your Android device.
   - Connect the device via USB and authorize the ADB connection.

4. **Ensure Your Device is Rooted**:
   Frida requires root access to function properly. Verify root access by running:
   ```bash
   adb shell su -c "id"
   ```

## Usage

To run the script, execute the following command:

```bash
python3 F-For-Frida-v3.py
```

### Script Flow

1. **Check Device Connection**: The script first checks if your Android device is connected and authorized.
   
2. **Root Access Confirmation**: It verifies if the connected device has root access.

3. **Frida Server Check**:
   - The script checks if the Frida server is already running by checking the default port (27042).
   - If the Frida server is running, the script will list the PIDs of all Frida server processes.
   - The user is then prompted to stop any running Frida server instances.

4. **Architecture Detection**:
   - The script automatically detects the architecture of the connected device (e.g., `arm64`, `x86_64`, etc.).
   
5. **Frida Server Version Management**:
   - The script prompts the user to enter the desired Frida version. It checks if the correct version of the Frida server is installed on the device.
   - If not installed, the script downloads and installs the correct version.

6. **Starting the Frida Server**:
   - The user is prompted to start the Frida server. If confirmed, the script starts the Frida server on the device and verifies if it is running successfully.

### Example

```bash
[*] Checking if a device is connected...
[+] Device connected and authorized.
[*] Checking if the device is rooted...
[+] Root access confirmed!
[*] Checking if Frida is running on the default port...
[+] Frida server is running on port 27042.
[+] Found Frida server PIDs: 5028, 5029, 5042
[*] Stopping all Frida server processes...
[*] Frida server processes stopped.
Enter the Frida version you want to use or install (e.g., 16.1.17): 16.0.1
[*] Checking if Frida server is installed...
[+] Frida server binary found.
[*] Do you want to run the Frida server now? (y/n): y
[*] Starting Frida server...
[+] Frida server started successfully with PID 5826.
```

## Troubleshooting

### Issue: Stuck on Starting Frida Server
- Ensure that your device is rooted.
- Check if **SELinux** is enforcing restrictive policies by temporarily disabling it:
  ```bash
  adb shell su -c "setenforce 0"
  ```

### Issue: Frida Server Fails to Start
- Check the logs using the following command:
  ```bash
  adb logcat | grep frida
  ```
- Ensure that the correct version of the Frida server is installed for the device architecture.

### Issue: Permissions Error
- Ensure that the Frida server binary has executable permissions:
  ```bash
  adb shell chmod 755 /data/local/tmp/frida-server-<version>-android-<arch>
  ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Let me know if you need any modifications or additional information!
