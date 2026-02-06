"""
ADB Client - Handles all ADB communication with Android devices
"""

import subprocess
from typing import Optional, Tuple, List
from dataclasses import dataclass

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Device:
    """Represents a connected Android device"""
    serial: str
    status: str
    model: Optional[str] = None
    architecture: Optional[str] = None
    
    @property
    def is_authorized(self) -> bool:
        return self.status == "device"
    
    @property
    def is_unauthorized(self) -> bool:
        return self.status == "unauthorized"
    
    def __str__(self) -> str:
        return f"{self.serial} ({self.model or 'Unknown'}) - {self.status}"


class ADBClient:
    """
    ADB Client for managing device connections and executing commands.
    Supports targeting specific devices for multi-device scenarios.
    """
    
    FRIDA_PORT = 27042
    
    def __init__(self, device_serial: Optional[str] = None):
        """
        Initialize ADB client.
        
        Args:
            device_serial: Optional device serial to target specific device.
                          If None, uses default device (fails if multiple connected).
        """
        self.device_serial = device_serial
    
    def _build_adb_command(self, args: List[str]) -> List[str]:
        """Build ADB command with optional device serial."""
        cmd = ["adb"]
        if self.device_serial:
            cmd.extend(["-s", self.device_serial])
        cmd.extend(args)
        return cmd
    
    def run_command(
        self, 
        args: List[str], 
        timeout: Optional[int] = None,
        check: bool = False
    ) -> Tuple[str, str, int]:
        """
        Execute an ADB command.
        
        Args:
            args: Command arguments (without 'adb' prefix)
            timeout: Command timeout in seconds
            check: If True, raises exception on non-zero return code
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        cmd = self._build_adb_command(args)
        logger.debug(f"Executing: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=check
            )
            stdout = result.stdout.decode('utf-8').strip()
            stderr = result.stderr.decode('utf-8').strip()
            return stdout, stderr, result.returncode
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {' '.join(cmd)}")
            return "", "Command timed out", -1
        except subprocess.CalledProcessError as e:
            return e.stdout.decode('utf-8').strip(), e.stderr.decode('utf-8').strip(), e.returncode
    
    def shell(self, command: str, su: bool = False, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        """
        Execute a shell command on the device.
        
        Args:
            command: Shell command to execute
            su: If True, executes command with superuser privileges
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if su:
            args = ["shell", "su", "-c", command]
        else:
            args = ["shell", command]
        return self.run_command(args, timeout=timeout)
    
    def shell_su(self, command: str, timeout: Optional[int] = None) -> Tuple[str, str, int]:
        """Execute a shell command with superuser privileges."""
        return self.shell(command, su=True, timeout=timeout)
    
    def push(self, local_path: str, remote_path: str) -> bool:
        """
        Push a file to the device.
        
        Args:
            local_path: Path to local file
            remote_path: Destination path on device
            
        Returns:
            True if successful, False otherwise
        """
        stdout, stderr, rc = self.run_command(["push", local_path, remote_path])
        if rc != 0:
            logger.error(f"Failed to push file: {stderr}")
            return False
        return True
    
    def pull(self, remote_path: str, local_path: str) -> bool:
        """
        Pull a file from the device.
        
        Args:
            remote_path: Path on device
            local_path: Destination local path
            
        Returns:
            True if successful, False otherwise
        """
        stdout, stderr, rc = self.run_command(["pull", remote_path, local_path])
        if rc != 0:
            logger.error(f"Failed to pull file: {stderr}")
            return False
        return True
    
    def get_property(self, prop: str) -> Optional[str]:
        """Get a device property value."""
        stdout, stderr, rc = self.shell(f"getprop {prop}")
        return stdout if rc == 0 and stdout else None
    
    @staticmethod
    def list_devices() -> List[Device]:
        """
        List all connected devices.
        
        Returns:
            List of Device objects
        """
        result = subprocess.run(
            ["adb", "devices", "-l"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output = result.stdout.decode('utf-8').strip()
        devices = []
        
        for line in output.splitlines()[1:]:  # Skip header
            if not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = parts[1]
                
                # Extract model from the line
                model = None
                for part in parts[2:]:
                    if part.startswith("model:"):
                        model = part.split(":")[1]
                        break
                
                devices.append(Device(serial=serial, status=status, model=model))
        
        return devices
    
    def check_root(self) -> bool:
        """
        Check if the device has root access.
        
        Returns:
            True if device is rooted, False otherwise
        """
        stdout, stderr, rc = self.shell("id", su=True, timeout=10)
        return "uid=0(root)" in stdout
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists on the device."""
        stdout, stderr, rc = self.shell(f"ls {path}")
        return "No such file" not in stderr and rc == 0
    
    def chmod(self, path: str, mode: str) -> bool:
        """Change file permissions on device."""
        stdout, stderr, rc = self.shell(f"chmod {mode} {path}")
        return rc == 0
