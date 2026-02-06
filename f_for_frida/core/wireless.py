"""
Wireless ADB Support for F-for-Frida
Enables TCP/IP connections to Android devices
"""

import re
import time
import subprocess
from typing import Optional, Tuple, List
from dataclasses import dataclass

from .adb import ADBClient, Device
from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


@dataclass
class WirelessDevice:
    """Represents a wireless ADB device"""
    ip: str
    port: int
    serial: str
    connected: bool = False
    
    @property
    def address(self) -> str:
        return f"{self.ip}:{self.port}"
    
    def __str__(self) -> str:
        status = "connected" if self.connected else "disconnected"
        return f"{self.address} ({status})"


class WirelessADB:
    """
    Manages wireless ADB connections.
    Supports connecting, disconnecting, and pairing devices over WiFi.
    """
    
    DEFAULT_PORT = 5555
    PAIRING_PORT_RANGE = (37000, 44000)
    
    def __init__(self):
        self.config = get_config()
    
    @staticmethod
    def _run_adb(args: List[str], timeout: int = 30) -> Tuple[str, str, int]:
        """Run an ADB command."""
        try:
            result = subprocess.run(
                ["adb"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
            return (
                result.stdout.decode('utf-8').strip(),
                result.stderr.decode('utf-8').strip(),
                result.returncode
            )
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", str(e), -1
    
    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format."""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        octets = ip.split('.')
        return all(0 <= int(o) <= 255 for o in octets)
    
    @staticmethod
    def parse_address(address: str) -> Tuple[str, int]:
        """
        Parse address string into IP and port.
        
        Args:
            address: IP address with optional port (e.g., "192.168.1.100" or "192.168.1.100:5555")
            
        Returns:
            Tuple of (ip, port)
        """
        if ':' in address:
            ip, port_str = address.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = WirelessADB.DEFAULT_PORT
        else:
            ip = address
            port = WirelessADB.DEFAULT_PORT
        
        return ip, port
    
    def enable_tcpip(self, device_serial: Optional[str] = None, port: int = 5555) -> bool:
        """
        Enable TCP/IP mode on a USB-connected device.
        
        Args:
            device_serial: Device serial (USB). If None, uses default device.
            port: TCP port for ADB (default: 5555)
            
        Returns:
            True if successful
        """
        args = []
        if device_serial:
            args.extend(["-s", device_serial])
        args.extend(["tcpip", str(port)])
        
        stdout, stderr, rc = self._run_adb(args)
        
        if rc == 0 or "restarting in TCP mode" in stdout.lower():
            logger.info(f"TCP/IP mode enabled on port {port}")
            time.sleep(2)  # Wait for restart
            return True
        
        logger.error(f"Failed to enable TCP/IP: {stderr}")
        return False
    
    def connect(self, address: str, timeout: int = 10) -> Tuple[bool, str]:
        """
        Connect to a device over WiFi.
        
        Args:
            address: IP:PORT or just IP (default port 5555)
            timeout: Connection timeout in seconds
            
        Returns:
            Tuple of (success, message)
        """
        ip, port = self.parse_address(address)
        
        if not self.validate_ip(ip):
            return False, f"Invalid IP address: {ip}"
        
        target = f"{ip}:{port}"
        logger.info(f"Connecting to {target}...")
        
        stdout, stderr, rc = self._run_adb(["connect", target], timeout=timeout)
        output = stdout or stderr
        
        if "connected" in output.lower() and "unable" not in output.lower():
            logger.info(f"Connected to {target}")
            return True, f"Connected to {target}"
        elif "already connected" in output.lower():
            return True, f"Already connected to {target}"
        else:
            return False, f"Connection failed: {output}"
    
    def disconnect(self, address: Optional[str] = None) -> Tuple[bool, str]:
        """
        Disconnect from wireless device(s).
        
        Args:
            address: Specific address to disconnect. If None, disconnects all.
            
        Returns:
            Tuple of (success, message)
        """
        if address:
            ip, port = self.parse_address(address)
            target = f"{ip}:{port}"
            stdout, stderr, rc = self._run_adb(["disconnect", target])
        else:
            stdout, stderr, rc = self._run_adb(["disconnect"])
        
        output = stdout or stderr
        
        if rc == 0 or "disconnected" in output.lower():
            return True, f"Disconnected: {output}"
        return False, f"Disconnect failed: {output}"
    
    def pair(self, address: str, pairing_code: str) -> Tuple[bool, str]:
        """
        Pair with a device using wireless debugging (Android 11+).
        
        Args:
            address: IP:PORT for pairing (usually different from connection port)
            pairing_code: 6-digit pairing code from device
            
        Returns:
            Tuple of (success, message)
        """
        ip, port = self.parse_address(address)
        target = f"{ip}:{port}"
        
        logger.info(f"Pairing with {target}...")
        
        try:
            # Pairing requires interactive input
            process = subprocess.Popen(
                ["adb", "pair", target],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=f"{pairing_code}\n", timeout=30)
            
            output = stdout + stderr
            if "successfully paired" in output.lower():
                return True, f"Successfully paired with {target}"
            else:
                return False, f"Pairing failed: {output}"
                
        except subprocess.TimeoutExpired:
            process.kill()
            return False, "Pairing timed out"
        except Exception as e:
            return False, f"Pairing error: {e}"
    
    def get_device_ip(self, device_serial: Optional[str] = None) -> Optional[str]:
        """
        Get the WiFi IP address of a connected device.
        
        Args:
            device_serial: Device serial. If None, uses default device.
            
        Returns:
            IP address or None
        """
        adb = ADBClient(device_serial=device_serial)
        
        # Try wlan0 first
        stdout, stderr, rc = adb.shell("ip addr show wlan0")
        if rc == 0:
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', stdout)
            if match:
                return match.group(1)
        
        # Fallback to ifconfig
        stdout, stderr, rc = adb.shell("ifconfig wlan0")
        if rc == 0:
            match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', stdout)
            if match:
                return match.group(1)
        
        # Try getting from settings
        stdout, stderr, rc = adb.shell("settings get global wifi_ip")
        if rc == 0 and stdout and self.validate_ip(stdout):
            return stdout
        
        return None
    
    def get_wireless_devices(self) -> List[WirelessDevice]:
        """
        Get list of wireless devices (connected or saved).
        
        Returns:
            List of WirelessDevice objects
        """
        devices = []
        connected_serials = set()
        
        # Get currently connected devices
        for device in ADBClient.list_devices():
            if ':' in device.serial:  # Wireless device
                ip, port = self.parse_address(device.serial)
                devices.append(WirelessDevice(
                    ip=ip,
                    port=port,
                    serial=device.serial,
                    connected=device.is_authorized
                ))
                connected_serials.add(device.serial)
        
        # Add saved devices that aren't connected
        for saved in self.config.saved_wireless_devices:
            ip, port = self.parse_address(saved)
            serial = f"{ip}:{port}"
            if serial not in connected_serials:
                devices.append(WirelessDevice(
                    ip=ip,
                    port=port,
                    serial=serial,
                    connected=False
                ))
        
        return devices
    
    def setup_wireless(self, device_serial: Optional[str] = None, port: int = 5555) -> Tuple[bool, str]:
        """
        Complete wireless setup: get IP, enable TCP/IP, and provide connection info.
        
        Args:
            device_serial: USB device serial
            port: TCP port for ADB
            
        Returns:
            Tuple of (success, message with connection address)
        """
        # Get device IP
        ip = self.get_device_ip(device_serial)
        if not ip:
            return False, "Could not determine device IP. Is WiFi connected?"
        
        # Enable TCP/IP mode
        if not self.enable_tcpip(device_serial, port):
            return False, "Failed to enable TCP/IP mode"
        
        address = f"{ip}:{port}"
        
        # Try to connect
        success, msg = self.connect(address)
        
        if success:
            return True, f"Wireless setup complete! Device available at {address}"
        else:
            return True, f"TCP/IP enabled. Connect with: adb connect {address}"
    
    def auto_reconnect(self) -> List[Tuple[str, bool]]:
        """
        Try to reconnect to all saved wireless devices.
        
        Returns:
            List of (address, success) tuples
        """
        results = []
        
        for address in self.config.saved_wireless_devices:
            success, _ = self.connect(address, timeout=5)
            results.append((address, success))
        
        return results
