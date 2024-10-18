import os
import subprocess
import sys
import requests
import time
from tqdm import tqdm
import logging
from colorama import Fore, Style, init
from shutil import which

# Initialize colorama
init(autoreset=True)

# Logging configuration
logging.basicConfig(filename='frida_script.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if 'xz' is installed on the system
def check_xz_installed():
    if which("xz") is None:
        print(Fore.RED + "[-] Error: 'xz' command is not installed on your system. Please install it to continue.")
        sys.exit(1)

# Function to run ADB commands with SU privilege
def adb_shell_su(command):
    result = subprocess.run(f"adb shell su -c '{command}'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode('utf-8').strip(), result.stderr.decode('utf-8').strip()

# Function to check if a device is connected via ADB
def check_device_connected():
    print(Fore.CYAN + "[*] Checking if a device is connected...")
    result = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE)
    devices = result.stdout.decode('utf-8').splitlines()
    
    if len(devices) > 1:
        print(Fore.GREEN + "[+] Device connected.")
        return True
    else:
        print(Fore.RED + "[-] No device connected. Please connect a device and try again.")
        return False

# Function to check if the device is rooted using ADB
def check_root():
    print(Fore.CYAN + "[*] Checking if the device is rooted...")
    try:
        result = subprocess.run(["adb", "shell", "su", "-c", "id"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        stdout = result.stdout.decode('utf-8').strip()
        if "uid=0(root)" in stdout:
            print(Fore.GREEN + "[+] Root access confirmed!")
            return True
        else:
            print(Fore.RED + "[-] The device is not rooted or ADB root is not enabled.")
            return False
    except subprocess.TimeoutExpired:
        print(Fore.RED + "[-] Root check timed out. Ensure that the device is connected and ADB is enabled.")
        return False

# Function to download the Frida server
def download_frida_server(version, os_type, architecture):
    url = f"https://github.com/frida/frida/releases/download/{version}/frida-server-{version}-{os_type}-{architecture}.xz"
    local_filename = f"frida-server-{version}-{os_type}-{architecture}.xz"
    
    print(Fore.CYAN + f"[*] Downloading Frida server from: {url}")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            block_size = 1024
            t = tqdm(total=total_size, unit='iB', unit_scale=True)
            with open(local_filename, 'wb') as f:
                for data in r.iter_content(block_size):
                    t.update(len(data))
                    f.write(data)
            t.close()
        print(Fore.GREEN + f"[+] Download complete: {local_filename}")
        return local_filename
    except requests.exceptions.HTTPError as err:
        print(Fore.RED + f"[-] Failed to download frida-server: {err}")
        logging.error(f"Failed to download frida-server: {err}")
        return None

# Function to extract the .xz file
def extract_xz_file(file_path):
    extracted_file = file_path.rstrip(".xz")
    
    if os.path.exists(extracted_file):
        print(Fore.YELLOW + f"[!] {extracted_file} already exists. Overwriting it.")
    
    print(Fore.CYAN + f"[*] Extracting {file_path}...")
    try:
        subprocess.run(['xz', '--decompress', '-f', file_path], check=True)
        print(Fore.GREEN + f"[+] Extraction complete!")
        logging.info(f"Extracted: {file_path}")
        return extracted_file
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[-] Failed to extract {file_path}: {e}")
        logging.error(f"Failed to extract {file_path}: {e}")
        return None

# Function to check if Frida is installed locally
def check_frida_installed():
    try:
        result = subprocess.run(["frida", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode("utf-8").strip()
    except FileNotFoundError:
        print(Fore.RED + "[-] Frida is not installed on your local machine.")
        return None

# Function to install Frida and Frida-tools locally
def install_frida_and_tools(version):
    print(Fore.CYAN + f"[*] Installing Frida {version} and frida-tools...")
    for _ in tqdm(range(100), desc="Installing Frida"):
        time.sleep(0.05)
    subprocess.run([sys.executable, "-m", "pip", "install", f"frida=={version}"])
    subprocess.run([sys.executable, "-m", "pip", "install", "frida-tools"])
    print(Fore.GREEN + f"[+] Frida {version} and frida-tools successfully installed!")
    logging.info(f"Frida {version} and frida-tools installed.")

# Validate if the entered Frida version exists on PyPi
def validate_frida_version(version):
    try:
        url = "https://pypi.org/pypi/frida/json"
        response = requests.get(url)
        available_versions = response.json()['releases'].keys()
        if version in available_versions:
            return True
        else:
            print(Fore.YELLOW + "[!] Invalid version. Available versions are:")
            print(Fore.YELLOW + ", ".join(sorted(available_versions, reverse=True)[:5]))
            return False
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[-] Error checking Frida versions: {e}")
        logging.error(f"Error checking Frida versions: {e}")
        return False

# Get device architecture
def get_device_architecture():
    print(Fore.CYAN + "[*] Detecting device architecture...")
    try:
        result = subprocess.run(["adb", "shell", "getprop", "ro.product.cpu.abi"], stdout=subprocess.PIPE, timeout=10)
        arch = result.stdout.decode("utf-8").strip()

        if arch in ["arm64-v8a", "arm64"]:
            print(Fore.GREEN + f"[+] Device architecture: {arch} (arm64)")
            return "arm64"
        elif arch in ["armeabi-v7a", "armeabi"]:
            print(Fore.GREEN + f"[+] Device architecture: {arch} (arm)")
            return "arm"
        elif arch in ["x86"]:
            print(Fore.GREEN + f"[+] Device architecture: {arch} (x86)")
            return "x86"
        elif arch in ["x86_64"]:
            print(Fore.GREEN + f"[+] Device architecture: {arch} (x86_64)")
            return "x86_64"
        else:
            print(Fore.RED + f"[-] Unknown architecture: {arch}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print(Fore.RED + "[-] Device architecture detection timed out.")
        sys.exit(1)

# Check Frida version on the connected device using the frida-server binary
def check_frida_version_on_device(frida_server_path):
    try:
        command = f"adb shell su -c '{frida_server_path} --version'"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode("utf-8").strip()
        if stdout:
            print(Fore.GREEN + f"[+] Frida server version on device: {stdout}")
            return stdout
        else:
            print(Fore.RED + "[-] Frida server is not running on the device.")
            return None
    except FileNotFoundError:
        print(Fore.RED + "[-] Frida server binary not found on the device.")
        return None

# Function to check if the Frida server is running on the device
def is_frida_server_running():
    print(Fore.CYAN + "[*] Checking if Frida server is running on the device...")
    try:
        result = subprocess.run(["adb", "shell", "ps", "|", "grep", "frida-server"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8').strip()
        if "frida-server" in stdout:
            print(Fore.GREEN + "[+] Frida server is running.")
            logging.info("Frida server is running.")
            return True
        else:
            print(Fore.RED + "[-] Frida server is not running.")
            logging.warning("Frida server is not running.")
            return False
    except Exception as e:
        print(Fore.RED + f"[-] Error checking Frida server status: {e}")
        logging.error(f"Error checking Frida server status: {e}")
        return False

# Ensure Frida versions match between local machine and device
def ensure_frida_version_compatibility(local_version, device_version):
    if local_version == device_version:
        print(Fore.GREEN + "[+] Frida versions match between the local machine and device.")
        logging.info("Frida versions match.")
        return True
    else:
        print(Fore.RED + f"[-] Version mismatch: Local Frida version {local_version} vs Device Frida version {device_version}.")
        logging.warning(f"Version mismatch: Local Frida version {local_version} vs Device Frida version {device_version}.")
        return False

# Get the port that Frida is running on
def get_frida_port():
    try:
        result = subprocess.run(["adb", "shell", "netstat", "-tuln"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8').strip().splitlines()
        for line in output:
            if "frida" in line:
                port_info = line.split()[3]  # Extract the port
                port = port_info.split(':')[-1]
                print(Fore.GREEN + f"[+] Frida server is running on port {port}.")
                logging.info(f"Frida server is running on port {port}.")
                return port
        print(Fore.RED + "[-] Could not find the port Frida is running on.")
        logging.warning("Could not find the port Frida is running on.")
        return None
    except Exception as e:
        print(Fore.RED + f"[-] Error fetching Frida port: {e}")
        logging.error(f"Error fetching Frida port: {e}")
        return None

# Install and run frida-server on a connected device based on the architecture
def install_frida_on_device(version, os_type, architecture):
    check_xz_installed()
    
    frida_server_path_on_device = f"/data/local/tmp/frida-server-{version}-android-{architecture}"
    
    device_frida_version = check_frida_version_on_device(frida_server_path_on_device)
    
    if device_frida_version:
        if device_frida_version == version:
            print(Fore.GREEN + f"[+] Frida version {version} is already installed and running on the device.")
            return
        else:
            print(Fore.YELLOW + f"[!] Frida version {device_frida_version} found, but it is not the desired version {version}.")
    else:
        print(Fore.CYAN + f"[*] Frida server is not found on the device. Proceeding to install...")
    
    downloaded_file = download_frida_server(version, os_type, architecture)
    if not downloaded_file:
        print(Fore.RED + "[-] Download failed, unable to install frida-server.")
        return
    
    extracted_file = extract_xz_file(downloaded_file)
    if not extracted_file:
        print(Fore.RED + "[-] Extraction failed, unable to install frida-server.")
        return

    subprocess.run(["adb", "push", extracted_file, frida_server_path_on_device])
    subprocess.run(["adb", "shell", "chmod", "755", frida_server_path_on_device])
    
    print(Fore.GREEN + f"[+] Frida {version} installed on the device in {frida_server_path_on_device}.")
    
    run_frida_server(frida_server_path_on_device)

# Run Frida server with root privileges, allowing user to specify a custom port
def run_frida_server(frida_server_path):
    custom_port = None
    use_custom_port = input(Fore.CYAN + "[*] Do you want to run Frida on a custom port? (y/n): ").strip().lower()
    if use_custom_port == 'y':
        custom_port = input(Fore.CYAN + "[*] Enter the custom port you want to run Frida on: ").strip()
        command = f"adb shell su -c '{frida_server_path} -l 127.0.0.1:{custom_port} &'"
    else:
        command = f"adb shell su -c '{frida_server_path} &'"
    
    print(Fore.CYAN + f"[*] Starting Frida server at {frida_server_path} with root privileges...")
    
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode("utf-8").strip()
        stderr = result.stderr.decode("utf-8").strip()

        if stdout:
            print(Fore.GREEN + "[+] Frida server started successfully.")
        if stderr:
            print(Fore.RED + f"[-] Error starting Frida server: {stderr}")
        
        # Check if the Frida server is running in a parallel session
        if is_frida_server_running():
            logging.info("Frida server is up and running.")
        else:
            logging.error("Failed to start Frida server.")
        
        # Display the port Frida is running on
        if not custom_port:
            get_frida_port()
        else:
            print(Fore.GREEN + f"[+] Frida server is running on custom port {custom_port}.")
            logging.info(f"Frida server running on custom port {custom_port}.")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[-] Failed to start Frida server: {e}")

# Function to stop the Frida server
def stop_frida_server(frida_server_path):
    print(Fore.CYAN + "[*] Stopping Frida server...")
    command = f"adb shell su -c 'killall frida-server'"
    try:
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(Fore.GREEN + "[+] Frida server stopped successfully.")
        logging.info("Frida server stopped successfully.")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[-] Failed to stop Frida server: {e}")
        logging.error(f"Failed to stop Frida server: {e}")

# Main script logic
def main():
    if not check_device_connected():
        return
    
    if not check_root():
        return
    
    desired_version = input(Fore.CYAN + "[*] Enter the Frida version you want to use or install (e.g., 16.1.17): ")
    
    if not validate_frida_version(desired_version):
        print(Fore.RED + "[-] Invalid Frida version. Exiting.")
        return
    
    local_frida_version = check_frida_installed()
    if local_frida_version:
        print(Fore.GREEN + f"[+] Frida version {local_frida_version} is already installed on your machine.")
    else:
        install_frida_and_tools(desired_version)

    device_arch = get_device_architecture()
    
    install_frida_on_device(desired_version, "android", device_arch)

    device_frida_version = check_frida_version_on_device(f"/data/local/tmp/frida-server-{desired_version}-android-{device_arch}")
    
    # Ensure Frida versions on the local machine and device match
    if not ensure_frida_version_compatibility(local_frida_version, device_frida_version):
        print(Fore.RED + "[-] Frida versions do not match. Please install matching versions to continue.")
        return

    # Prompt user if they want to stop the Frida server
    while True:
        user_input = input(Fore.CYAN + "[*] Do you want to stop the Frida server? (y/n): ").strip().lower()
        if user_input == 'y':
            frida_server_path = f"/data/local/tmp/frida-server-{desired_version}-android-{device_arch}"
            stop_frida_server(frida_server_path)
            break
        elif user_input == 'n':
            print(Fore.GREEN + "[+] Exiting script while keeping Frida server running.")
            break
        else:
            print(Fore.YELLOW + "[!] Invalid input. Please enter 'y' or 'n'.")

if __name__ == "__main__":
    main()
