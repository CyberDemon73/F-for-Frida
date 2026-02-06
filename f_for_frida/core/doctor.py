"""
Doctor / Health Check Module for F-for-Frida
Diagnoses common issues and provides solutions
"""

import os
import subprocess
import platform
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from shutil import which

from .adb import ADBClient
from .device import DeviceManager
from .frida_manager import FridaManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CheckStatus(Enum):
    """Status of a health check"""
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    """Result of a health check"""
    name: str
    status: CheckStatus
    message: str
    fix: Optional[str] = None
    
    @property
    def icon(self) -> str:
        icons = {
            CheckStatus.OK: "✓",
            CheckStatus.WARNING: "!",
            CheckStatus.ERROR: "✗",
            CheckStatus.SKIPPED: "○",
        }
        return icons[self.status]


class Doctor:
    """
    Diagnoses common issues with the F-for-Frida setup.
    Checks system requirements, device status, and Frida server health.
    """
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.results: List[CheckResult] = []
    
    def _add_result(self, name: str, status: CheckStatus, message: str, fix: Optional[str] = None):
        """Add a check result."""
        self.results.append(CheckResult(name, status, message, fix))
    
    def check_python_version(self) -> CheckResult:
        """Check Python version."""
        import sys
        version = sys.version_info
        
        if version >= (3, 8):
            return CheckResult(
                "Python Version",
                CheckStatus.OK,
                f"Python {version.major}.{version.minor}.{version.micro}"
            )
        else:
            return CheckResult(
                "Python Version",
                CheckStatus.ERROR,
                f"Python {version.major}.{version.minor} (3.8+ required)",
                "Upgrade Python to version 3.8 or higher"
            )
    
    def check_adb_installed(self) -> CheckResult:
        """Check if ADB is installed and accessible."""
        if which("adb"):
            try:
                result = subprocess.run(
                    ["adb", "version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = result.stdout.split('\n')[0] if result.stdout else "Unknown"
                return CheckResult(
                    "ADB Installation",
                    CheckStatus.OK,
                    version
                )
            except Exception:
                pass
        
        fix = {
            "Windows": "Install Android SDK Platform Tools or run: winget install Google.PlatformTools",
            "Darwin": "Install with: brew install android-platform-tools",
            "Linux": "Install with: sudo apt install adb"
        }.get(platform.system(), "Install Android SDK Platform Tools")
        
        return CheckResult(
            "ADB Installation",
            CheckStatus.ERROR,
            "ADB not found in PATH",
            fix
        )
    
    def check_xz_installed(self) -> CheckResult:
        """Check if XZ Utils is installed."""
        if which("xz"):
            return CheckResult(
                "XZ Utils",
                CheckStatus.OK,
                "XZ compression tool available"
            )
        
        fix = {
            "Windows": "Install with: winget install xz",
            "Darwin": "Install with: brew install xz",
            "Linux": "Install with: sudo apt install xz-utils"
        }.get(platform.system(), "Install XZ Utils")
        
        return CheckResult(
            "XZ Utils",
            CheckStatus.ERROR,
            "XZ not found (needed to extract Frida server)",
            fix
        )
    
    def check_device_connected(self) -> CheckResult:
        """Check if any device is connected."""
        devices = ADBClient.list_devices()
        
        if not devices:
            return CheckResult(
                "Device Connection",
                CheckStatus.ERROR,
                "No devices connected",
                "Connect a device via USB and enable USB debugging"
            )
        
        authorized = [d for d in devices if d.is_authorized]
        unauthorized = [d for d in devices if d.is_unauthorized]
        
        if authorized:
            return CheckResult(
                "Device Connection",
                CheckStatus.OK,
                f"{len(authorized)} device(s) connected and authorized"
            )
        elif unauthorized:
            return CheckResult(
                "Device Connection",
                CheckStatus.WARNING,
                f"{len(unauthorized)} device(s) need authorization",
                "Accept the USB debugging prompt on your device"
            )
        else:
            return CheckResult(
                "Device Connection",
                CheckStatus.WARNING,
                f"{len(devices)} device(s) in unknown state"
            )
    
    def check_device_root(self) -> CheckResult:
        """Check if device is rooted."""
        dm = DeviceManager()
        serial = dm.select_device(self.device_serial)
        
        if not serial:
            return CheckResult(
                "Root Access",
                CheckStatus.SKIPPED,
                "No device available to check"
            )
        
        adb = ADBClient(device_serial=serial)
        if adb.check_root():
            return CheckResult(
                "Root Access",
                CheckStatus.OK,
                "Device has root access"
            )
        else:
            return CheckResult(
                "Root Access",
                CheckStatus.ERROR,
                "Device is not rooted or root not granted",
                "Root your device or grant root access to ADB"
            )
    
    def check_selinux(self) -> CheckResult:
        """Check SELinux status."""
        dm = DeviceManager()
        serial = dm.select_device(self.device_serial)
        
        if not serial:
            return CheckResult(
                "SELinux",
                CheckStatus.SKIPPED,
                "No device available to check"
            )
        
        adb = ADBClient(device_serial=serial)
        stdout, stderr, rc = adb.shell("getenforce")
        
        if "Permissive" in stdout:
            return CheckResult(
                "SELinux",
                CheckStatus.OK,
                "SELinux is Permissive"
            )
        elif "Enforcing" in stdout:
            return CheckResult(
                "SELinux",
                CheckStatus.WARNING,
                "SELinux is Enforcing (may block Frida)",
                "Consider running: adb shell su -c 'setenforce 0'"
            )
        else:
            return CheckResult(
                "SELinux",
                CheckStatus.OK,
                f"SELinux status: {stdout or 'Unknown'}"
            )
    
    def check_frida_server(self) -> CheckResult:
        """Check Frida server status."""
        dm = DeviceManager()
        serial = dm.select_device(self.device_serial)
        
        if not serial:
            return CheckResult(
                "Frida Server",
                CheckStatus.SKIPPED,
                "No device available to check"
            )
        
        fm = FridaManager(device_serial=serial)
        status = fm.get_server_status()
        
        if status['running'] and status['port_listening']:
            return CheckResult(
                "Frida Server",
                CheckStatus.OK,
                f"Running and listening on port 27042"
            )
        elif status['running']:
            return CheckResult(
                "Frida Server",
                CheckStatus.WARNING,
                "Running but not listening on default port",
                "Try restarting the Frida server"
            )
        elif status['installed_servers']:
            return CheckResult(
                "Frida Server",
                CheckStatus.WARNING,
                "Installed but not running",
                "Start the server with: f4f start"
            )
        else:
            return CheckResult(
                "Frida Server",
                CheckStatus.ERROR,
                "Not installed",
                "Install with: f4f install --latest"
            )
    
    def check_frida_client(self) -> CheckResult:
        """Check if Frida tools are installed on host."""
        try:
            import frida
            version = frida.__version__
            return CheckResult(
                "Frida Client",
                CheckStatus.OK,
                f"Frida tools v{version} installed"
            )
        except ImportError:
            return CheckResult(
                "Frida Client",
                CheckStatus.WARNING,
                "Frida tools not installed on host",
                "Install with: pip install frida-tools"
            )
    
    def check_usb_debugging(self) -> CheckResult:
        """Check USB debugging status."""
        dm = DeviceManager()
        serial = dm.select_device(self.device_serial)
        
        if not serial:
            return CheckResult(
                "USB Debugging",
                CheckStatus.SKIPPED,
                "No device available"
            )
        
        # If we got this far, USB debugging is enabled
        return CheckResult(
            "USB Debugging",
            CheckStatus.OK,
            "USB debugging is enabled"
        )
    
    def check_disk_space(self) -> CheckResult:
        """Check available disk space on device."""
        dm = DeviceManager()
        serial = dm.select_device(self.device_serial)
        
        if not serial:
            return CheckResult(
                "Device Storage",
                CheckStatus.SKIPPED,
                "No device available"
            )
        
        adb = ADBClient(device_serial=serial)
        stdout, stderr, rc = adb.shell("df /data/local/tmp | tail -1")
        
        if rc == 0 and stdout:
            parts = stdout.split()
            if len(parts) >= 4:
                available = parts[3]
                return CheckResult(
                    "Device Storage",
                    CheckStatus.OK,
                    f"Available space in /data/local/tmp: {available}"
                )
        
        return CheckResult(
            "Device Storage",
            CheckStatus.WARNING,
            "Could not determine available space"
        )
    
    def run_all_checks(self) -> List[CheckResult]:
        """Run all health checks."""
        self.results = []
        
        checks = [
            self.check_python_version,
            self.check_adb_installed,
            self.check_xz_installed,
            self.check_device_connected,
            self.check_usb_debugging,
            self.check_device_root,
            self.check_selinux,
            self.check_frida_server,
            self.check_frida_client,
            self.check_disk_space,
        ]
        
        for check in checks:
            try:
                result = check()
                self.results.append(result)
            except Exception as e:
                self.results.append(CheckResult(
                    check.__name__.replace("check_", "").replace("_", " ").title(),
                    CheckStatus.ERROR,
                    f"Check failed: {e}"
                ))
        
        return self.results
    
    def get_summary(self) -> Tuple[int, int, int, int]:
        """Get summary counts (ok, warning, error, skipped)."""
        ok = sum(1 for r in self.results if r.status == CheckStatus.OK)
        warning = sum(1 for r in self.results if r.status == CheckStatus.WARNING)
        error = sum(1 for r in self.results if r.status == CheckStatus.ERROR)
        skipped = sum(1 for r in self.results if r.status == CheckStatus.SKIPPED)
        return ok, warning, error, skipped
    
    def has_errors(self) -> bool:
        """Check if any critical errors were found."""
        return any(r.status == CheckStatus.ERROR for r in self.results)
    
    def get_fixes(self) -> List[Tuple[str, str]]:
        """Get list of suggested fixes for issues."""
        fixes = []
        for r in self.results:
            if r.fix and r.status in [CheckStatus.ERROR, CheckStatus.WARNING]:
                fixes.append((r.name, r.fix))
        return fixes
