"""
Frida Manager - Handles Frida server installation and management
"""

import os
import time
import subprocess
from typing import Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

from .adb import ADBClient
from ..utils.logger import get_logger
from ..utils.downloader import download_frida_server, get_latest_frida_version

logger = get_logger(__name__)


@dataclass
class FridaServerInfo:
    """Information about a Frida server instance"""
    pid: int
    path: str
    version: Optional[str] = None


class FridaManager:
    """
    Manages Frida server installation, starting, and stopping on Android devices.
    """
    
    FRIDA_PORT = 27042
    FRIDA_PATH_TEMPLATE = "/data/local/tmp/frida-server-{version}-android-{arch}"
    
    def __init__(self, device_serial: Optional[str] = None):
        """
        Initialize Frida Manager.
        
        Args:
            device_serial: Target device serial number
        """
        self.device_serial = device_serial
        self.adb = ADBClient(device_serial=device_serial)
    
    def get_running_servers(self) -> List[FridaServerInfo]:
        """
        Get list of running Frida server instances.
        
        Returns:
            List of FridaServerInfo objects
        """
        stdout, stderr, rc = self.adb.shell("ps -Af | grep frida-server")
        servers = []
        
        if rc != 0 or not stdout:
            return servers
        
        for line in stdout.splitlines():
            if "frida-server" in line and "grep" not in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        # Get the path (usually the last column)
                        path = parts[-1] if "/" in parts[-1] else ""
                        servers.append(FridaServerInfo(pid=pid, path=path))
                    except (ValueError, IndexError):
                        continue
        
        return servers
    
    def is_server_running(self) -> bool:
        """Check if any Frida server is running."""
        return len(self.get_running_servers()) > 0
    
    def check_port_listening(self) -> bool:
        """Check if Frida is listening on the default port."""
        stdout, stderr, rc = self.adb.shell(f"netstat -tuln | grep {self.FRIDA_PORT}")
        return bool(stdout.strip())
    
    def stop_server(self, pid: Optional[int] = None) -> bool:
        """
        Stop Frida server(s).
        
        Args:
            pid: Specific PID to stop. If None, stops all Frida servers.
            
        Returns:
            True if successful
        """
        if pid:
            pids = [pid]
        else:
            servers = self.get_running_servers()
            pids = [s.pid for s in servers]
        
        if not pids:
            logger.info("No Frida servers running")
            return True
        
        success = True
        for p in pids:
            logger.info(f"Stopping Frida server PID {p}")
            stdout, stderr, rc = self.adb.shell_su(f"kill -9 {p}")
            if rc != 0:
                logger.error(f"Failed to stop PID {p}: {stderr}")
                success = False
        
        return success
    
    def stop_all_servers(self) -> bool:
        """Stop all running Frida server instances."""
        return self.stop_server(pid=None)
    
    def is_server_installed(self, version: str, architecture: str) -> Optional[str]:
        """
        Check if a specific Frida server version is installed.
        
        Args:
            version: Frida version
            architecture: Device architecture (arm64, arm, x86, x86_64)
            
        Returns:
            Server path if installed, None otherwise
        """
        path = self.FRIDA_PATH_TEMPLATE.format(version=version, arch=architecture)
        if self.adb.file_exists(path):
            return path
        return None
    
    def list_installed_servers(self) -> List[str]:
        """
        List all installed Frida server versions.
        
        Returns:
            List of installed server paths
        """
        stdout, stderr, rc = self.adb.shell("ls /data/local/tmp/frida-server-* 2>/dev/null")
        if rc != 0 or not stdout:
            return []
        return [line.strip() for line in stdout.splitlines() if line.strip()]
    
    def install_server(
        self, 
        version: str, 
        architecture: str,
        download_dir: Optional[str] = None,
        force: bool = False
    ) -> Optional[str]:
        """
        Download and install Frida server on the device.
        
        Args:
            version: Frida version to install
            architecture: Device architecture
            download_dir: Directory to save downloaded files
            force: Force reinstall even if already installed
            
        Returns:
            Installed server path or None on failure
        """
        # Check if already installed
        existing_path = self.is_server_installed(version, architecture)
        if existing_path and not force:
            logger.info(f"Frida server {version} already installed at {existing_path}")
            return existing_path
        
        # Download the server
        download_dir = download_dir or os.getcwd()
        local_path = download_frida_server(version, architecture, download_dir)
        
        if not local_path:
            logger.error("Failed to download Frida server")
            return None
        
        # Push to device
        remote_path = self.FRIDA_PATH_TEMPLATE.format(version=version, arch=architecture)
        
        logger.info(f"Pushing Frida server to {remote_path}")
        if not self.adb.push(local_path, remote_path):
            logger.error("Failed to push Frida server to device")
            return None
        
        # Set permissions
        if not self.adb.chmod(remote_path, "755"):
            logger.error("Failed to set permissions on Frida server")
            return None
        
        logger.info(f"Frida server {version} installed successfully")
        
        # Clean up local file
        try:
            os.remove(local_path)
        except OSError:
            pass
        
        return remote_path
    
    def start_server(
        self, 
        server_path: str,
        wait_for_start: bool = True,
        timeout: int = 10
    ) -> Tuple[bool, Optional[int]]:
        """
        Start Frida server on the device.
        
        Args:
            server_path: Path to Frida server binary on device
            wait_for_start: Wait and verify server started
            timeout: Timeout for waiting
            
        Returns:
            Tuple of (success, pid)
        """
        logger.info(f"Starting Frida server from {server_path}")
        
        # Start server in background
        start_cmd = f"nohup {server_path} >/dev/null 2>&1 &"
        self.adb.shell_su(start_cmd)
        
        if not wait_for_start:
            return True, None
        
        # Wait for server to start
        time.sleep(2)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            servers = self.get_running_servers()
            if servers:
                pid = servers[0].pid
                logger.info(f"Frida server started with PID {pid}")
                return True, pid
            time.sleep(1)
        
        logger.error("Failed to start Frida server (timeout)")
        return False, None
    
    def restart_server(self, server_path: str) -> Tuple[bool, Optional[int]]:
        """
        Restart Frida server.
        
        Args:
            server_path: Path to Frida server binary
            
        Returns:
            Tuple of (success, pid)
        """
        self.stop_all_servers()
        time.sleep(1)
        return self.start_server(server_path)
    
    def uninstall_server(self, version: str, architecture: str) -> bool:
        """
        Remove Frida server from device.
        
        Args:
            version: Frida version
            architecture: Device architecture
            
        Returns:
            True if successful
        """
        path = self.FRIDA_PATH_TEMPLATE.format(version=version, arch=architecture)
        stdout, stderr, rc = self.adb.shell(f"rm -f {path}")
        return rc == 0
    
    def get_server_status(self) -> dict:
        """
        Get comprehensive Frida server status.
        
        Returns:
            Dictionary with status information
        """
        servers = self.get_running_servers()
        port_listening = self.check_port_listening()
        installed = self.list_installed_servers()
        
        return {
            "running": len(servers) > 0,
            "port_listening": port_listening,
            "instances": [{"pid": s.pid, "path": s.path} for s in servers],
            "installed_servers": installed,
        }
