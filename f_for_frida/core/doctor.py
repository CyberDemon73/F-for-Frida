"""
Doctor / Health Check Module for F-for-Frida
Diagnoses common issues and provides solutions with fix options
"""

import os
import subprocess
import platform
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from shutil import which

from .adb import ADBClient
from .device import DeviceManager
from .frida_manager import FridaManager
from .compatibility import VersionChecker, VersionStatus, versions_compatible, get_android_codename
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
    fix_action: Optional[Callable] = None
    fix_args: dict = field(default_factory=dict)
    details: Optional[str] = None
    
    @property
    def icon(self) -> str:
        icons = {
            CheckStatus.OK: "✓",
            CheckStatus.WARNING: "!",
            CheckStatus.ERROR: "✗",
            CheckStatus.SKIPPED: "○",
        }
        return icons[self.status]
    
    @property
    def can_fix(self) -> bool:
        return self.fix_action is not None


class Doctor:
    """
    Diagnoses common issues with the F-for-Frida setup.
    Checks system requirements, device status, Frida server health,
    and version compatibility.
    """
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.results: List[CheckResult] = []
        self._version_checker: Optional[VersionChecker] = None
        self._device_info: Optional[dict] = None
    
    @property
    def version_checker(self) -> Optional[VersionChecker]:
        if self._version_checker is None and self.device_serial:
            self._version_checker = VersionChecker(device_serial=self.device_serial)
        return self._version_checker
    
    def _add_result(self, name: str, status: CheckStatus, message: str, 
                    fix: Optional[str] = None, fix_action: Optional[Callable] = None,
                    fix_args: dict = None, details: Optional[str] = None):
        """Add a check result."""
        self.results.append(CheckResult(
            name=name, 
            status=status, 
            message=message, 
            fix=fix,
            fix_action=fix_action,
            fix_args=fix_args or {},
            details=details
        ))
    
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
            # Store selected device for future checks
            if not self.device_serial:
                self.device_serial = authorized[0].serial
                self._version_checker = VersionChecker(device_serial=self.device_serial)
            
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
    
    def check_device_info(self) -> CheckResult:
        """Check and display device information."""
        if not self.version_checker:
            return CheckResult(
                "Device Info",
                CheckStatus.SKIPPED,
                "No device available"
            )
        
        info = self.version_checker.get_device_info()
        if not info:
            return CheckResult(
                "Device Info",
                CheckStatus.WARNING,
                "Could not retrieve device information"
            )
        
        self._device_info = info
        
        android_ver = info.get("android_version", 0)
        codename = get_android_codename(android_ver)
        
        details = (
            f"Model: {info.get('device_model', 'Unknown')}\n"
            f"Manufacturer: {info.get('manufacturer', 'Unknown')}\n"
            f"Android: {android_ver} ({codename})\n"
            f"SDK: {info.get('sdk_version', 'Unknown')}\n"
            f"Architecture: {info.get('frida_arch', 'Unknown')}\n"
            f"Build: {info.get('build_id', 'Unknown')}"
        )
        
        return CheckResult(
            "Device Info",
            CheckStatus.OK,
            f"Android {android_ver} ({codename}) - {info.get('frida_arch', 'Unknown')}",
            details=details
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
        
        def fix_selinux():
            adb.shell_su("setenforce 0")
            return True
        
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
                "Run: adb shell su -c 'setenforce 0'",
                fix_action=fix_selinux
            )
        else:
            return CheckResult(
                "SELinux",
                CheckStatus.OK,
                f"SELinux status: {stdout or 'Unknown'}"
            )
    
    def check_frida_client(self) -> CheckResult:
        """Check if Frida Python library is installed on host."""
        try:
            import frida
            version = frida.__version__
            return CheckResult(
                "Frida Python",
                CheckStatus.OK,
                f"v{version} installed"
            )
        except ImportError:
            def fix_frida_client():
                subprocess.run(["pip", "install", "frida"], check=True)
                return True
            
            return CheckResult(
                "Frida Python",
                CheckStatus.ERROR,
                "Not installed on host",
                "Run: pip install frida",
                fix_action=fix_frida_client
            )
    
    def check_frida_tools(self) -> CheckResult:
        """Check if frida-tools is installed on host."""
        if not self.version_checker:
            self._version_checker = VersionChecker()
        
        tools = self.version_checker.get_frida_tools_version()
        
        if tools.installed:
            return CheckResult(
                "Frida Tools",
                CheckStatus.OK,
                f"v{tools.version} installed"
            )
        else:
            def fix_frida_tools():
                subprocess.run(["pip", "install", "frida-tools"], check=True)
                return True
            
            return CheckResult(
                "Frida Tools",
                CheckStatus.WARNING,
                "Not installed on host",
                "Run: pip install frida-tools",
                fix_action=fix_frida_tools
            )
    
    def check_frida_server(self) -> CheckResult:
        """Check Frida server status on device."""
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
            # Get version
            if self.version_checker:
                server = self.version_checker.get_frida_server_version()
                version_str = f" v{server.version}" if server.version else ""
            else:
                version_str = ""
            
            return CheckResult(
                "Frida Server",
                CheckStatus.OK,
                f"Running{version_str} on port 27042"
            )
        elif status['running']:
            return CheckResult(
                "Frida Server",
                CheckStatus.WARNING,
                "Running but not listening on default port",
                "Try restarting: f4f restart"
            )
        elif status['installed_servers']:
            def fix_start_server():
                installed = fm.list_installed_servers()
                if installed:
                    success, _ = fm.start_server(installed[0])
                    return success
                return False
            
            return CheckResult(
                "Frida Server",
                CheckStatus.WARNING,
                "Installed but not running",
                "Run: f4f start",
                fix_action=fix_start_server
            )
        else:
            # Not installed - determine version to install based on client
            target_version = None
            target_msg = "latest"
            
            try:
                import frida
                target_version = frida.__version__
                target_msg = f"{target_version} (matches host client)"
            except ImportError:
                pass
            
            def fix_install_server():
                from .compatibility import VersionChecker
                from .device import DeviceManager as DM
                
                dm_inner = DM()
                info = dm_inner.get_device_info(serial)
                if not info:
                    return False
                
                # Get version to install (match client)
                version = target_version
                if not version:
                    try:
                        import frida
                        version = frida.__version__
                    except ImportError:
                        from ..utils.downloader import get_latest_frida_version
                        version = get_latest_frida_version()
                
                if version:
                    path = fm.install_server(version, info.frida_architecture, force=True)
                    if path:
                        # Start the server
                        fm.start_server(path)
                        return True
                return False
            
            return CheckResult(
                "Frida Server",
                CheckStatus.ERROR,
                f"Not installed (will install v{target_msg})",
                f"Run: f4f install {target_version or '--latest'}",
                fix_action=fix_install_server
            )
    
    def check_version_compatibility(self) -> CheckResult:
        """Check version compatibility between Frida components."""
        if not self.version_checker:
            return CheckResult(
                "Version Compatibility",
                CheckStatus.SKIPPED,
                "No device available"
            )
        
        compat = self.version_checker.check_compatibility()
        
        # Build details string
        details = (
            f"Frida Python: {compat.client_version or 'Not installed'}\n"
            f"Frida Tools: {compat.tools_version or 'Not installed'}\n"
            f"Frida Server: {compat.server_version or 'Not installed'}"
        )
        
        def fix_version():
            success, msg = self.version_checker.fix_version_mismatch()
            return success
        
        if compat.status == VersionStatus.MATCH:
            return CheckResult(
                "Version Compatibility",
                CheckStatus.OK,
                f"All versions match: {compat.client_version}",
                details=details
            )
        elif compat.status == VersionStatus.COMPATIBLE:
            return CheckResult(
                "Version Compatibility",
                CheckStatus.OK,
                compat.message,
                details=details
            )
        elif compat.status == VersionStatus.MISMATCH:
            return CheckResult(
                "Version Compatibility",
                CheckStatus.ERROR,
                compat.message,
                compat.fix_command,
                fix_action=fix_version,
                details=details
            )
        elif compat.status == VersionStatus.NOT_INSTALLED:
            return CheckResult(
                "Version Compatibility",
                CheckStatus.WARNING,
                compat.message,
                compat.fix_command,
                details=details
            )
        else:
            return CheckResult(
                "Version Compatibility",
                CheckStatus.WARNING,
                "Could not verify compatibility",
                details=details
            )
    
    def check_recommended_version(self) -> CheckResult:
        """Check if using recommended Frida version for device."""
        if not self.version_checker:
            return CheckResult(
                "Recommended Version",
                CheckStatus.SKIPPED,
                "No device available"
            )
        
        rec = self.version_checker.get_recommended_version()
        if not rec:
            return CheckResult(
                "Recommended Version",
                CheckStatus.WARNING,
                "Could not determine recommendation"
            )
        
        details = (
            f"Android: {rec.android_version} ({rec.android_codename})\n"
            f"Architecture: {rec.architecture}\n"
            f"Min Frida: {rec.min_frida_version}\n"
            f"Recommended: {rec.recommended_frida_version}\n"
            f"Current: {rec.current_server_version or 'Not installed'}"
        )
        
        if rec.notes:
            details += "\nNotes:\n" + "\n".join(f"  • {n}" for n in rec.notes)
        
        if not rec.current_server_version:
            return CheckResult(
                "Recommended Version",
                CheckStatus.WARNING,
                f"Install recommended: {rec.recommended_frida_version}",
                f"Run: f4f install {rec.recommended_frida_version}",
                details=details
            )
        
        # Check if current version meets minimum
        from .compatibility import parse_version
        current = parse_version(rec.current_server_version)
        minimum = parse_version(rec.min_frida_version)
        recommended = parse_version(rec.recommended_frida_version)
        
        if current >= recommended:
            return CheckResult(
                "Recommended Version",
                CheckStatus.OK,
                f"Using recommended version {rec.current_server_version}",
                details=details
            )
        elif current >= minimum:
            return CheckResult(
                "Recommended Version",
                CheckStatus.OK,
                f"Version {rec.current_server_version} compatible (recommended: {rec.recommended_frida_version})",
                details=details
            )
        else:
            def fix_version():
                from .frida_manager import FridaManager
                fm = FridaManager(device_serial=self.device_serial)
                path = fm.install_server(rec.recommended_frida_version, rec.architecture, force=True)
                return path is not None
            
            return CheckResult(
                "Recommended Version",
                CheckStatus.WARNING,
                f"Version {rec.current_server_version} is below minimum {rec.min_frida_version}",
                f"Run: f4f install {rec.recommended_frida_version}",
                fix_action=fix_version,
                details=details
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
                    f"Available: {available}"
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
            self.check_device_info,
            self.check_device_root,
            self.check_selinux,
            self.check_frida_client,
            self.check_frida_tools,
            self.check_frida_server,
            self.check_version_compatibility,
            self.check_recommended_version,
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
    
    def get_fixable_issues(self) -> List[CheckResult]:
        """Get list of issues that can be automatically fixed."""
        return [
            r for r in self.results 
            if r.can_fix and r.status in [CheckStatus.ERROR, CheckStatus.WARNING]
        ]
    
    def get_fixes(self) -> List[Tuple[str, str]]:
        """Get list of suggested fixes for issues."""
        fixes = []
        for r in self.results:
            if r.fix and r.status in [CheckStatus.ERROR, CheckStatus.WARNING]:
                fixes.append((r.name, r.fix))
        return fixes
    
    def apply_fix(self, result: CheckResult) -> Tuple[bool, str]:
        """
        Apply fix for a specific issue.
        
        Args:
            result: CheckResult with fix_action
            
        Returns:
            Tuple of (success, message)
        """
        if not result.can_fix:
            return False, "No automatic fix available"
        
        try:
            success = result.fix_action(**result.fix_args)
            if success:
                return True, f"Fixed: {result.name}"
            else:
                return False, f"Fix failed for: {result.name}"
        except Exception as e:
            return False, f"Fix error: {e}"
    
    def apply_all_fixes(self) -> List[Tuple[str, bool, str]]:
        """
        Apply all available fixes.
        
        Returns:
            List of (name, success, message) tuples
        """
        results = []
        for issue in self.get_fixable_issues():
            success, message = self.apply_fix(issue)
            results.append((issue.name, success, message))
        return results
