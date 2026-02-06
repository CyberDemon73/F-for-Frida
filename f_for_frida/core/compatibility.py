"""
Frida Version Compatibility Module
Handles version matching between server, client, and frida-tools
"""

import re
import subprocess
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum

from .adb import ADBClient
from .frida_manager import FridaManager
from ..utils.logger import get_logger
from ..utils.downloader import get_latest_frida_version, get_available_versions

logger = get_logger(__name__)


# Android version to recommended Frida version mapping
# Based on compatibility and stability
ANDROID_FRIDA_RECOMMENDATIONS = {
    # Android 14 (API 34)
    14: {"min": "16.0.0", "recommended": "16.1.17"},
    # Android 13 (API 33)
    13: {"min": "15.0.0", "recommended": "16.1.17"},
    # Android 12/12L (API 31-32)
    12: {"min": "15.0.0", "recommended": "16.1.17"},
    # Android 11 (API 30)
    11: {"min": "14.0.0", "recommended": "16.1.17"},
    # Android 10 (API 29)
    10: {"min": "12.8.0", "recommended": "16.1.17"},
    # Android 9 (API 28)
    9: {"min": "12.0.0", "recommended": "15.2.2"},
    # Android 8/8.1 (API 26-27)
    8: {"min": "10.0.0", "recommended": "15.2.2"},
    # Android 7/7.1 (API 24-25)
    7: {"min": "9.0.0", "recommended": "14.2.18"},
    # Android 6 (API 23)
    6: {"min": "8.0.0", "recommended": "12.11.18"},
    # Android 5/5.1 (API 21-22)
    5: {"min": "7.0.0", "recommended": "12.11.18"},
}


class VersionStatus(Enum):
    """Version compatibility status"""
    MATCH = "match"
    COMPATIBLE = "compatible"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    NOT_INSTALLED = "not_installed"


@dataclass
class VersionInfo:
    """Version information for a component"""
    component: str
    version: Optional[str]
    installed: bool
    
    def __str__(self) -> str:
        if not self.installed:
            return f"{self.component}: Not installed"
        return f"{self.component}: {self.version or 'Unknown'}"


@dataclass
class CompatibilityResult:
    """Result of compatibility check"""
    status: VersionStatus
    message: str
    server_version: Optional[str]
    client_version: Optional[str]
    tools_version: Optional[str]
    fix_command: Optional[str] = None
    
    @property
    def is_compatible(self) -> bool:
        return self.status in [VersionStatus.MATCH, VersionStatus.COMPATIBLE]


@dataclass 
class DeviceRecommendation:
    """Recommended Frida version for a device"""
    android_version: int
    android_codename: str
    sdk_version: int
    architecture: str
    min_frida_version: str
    recommended_frida_version: str
    current_server_version: Optional[str]
    notes: List[str]


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """
    Parse version string to tuple for comparison.
    
    Args:
        version_str: Version string like "16.1.17"
        
    Returns:
        Tuple of (major, minor, patch)
    """
    if not version_str:
        return (0, 0, 0)
    
    # Remove any prefix like 'v'
    version_str = version_str.lstrip('v')
    
    # Extract numbers
    match = re.match(r'(\d+)\.(\d+)\.?(\d+)?', version_str)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3)) if match.group(3) else 0
        return (major, minor, patch)
    
    return (0, 0, 0)


def versions_compatible(v1: str, v2: str, strict: bool = False) -> bool:
    """
    Check if two Frida versions are compatible.
    
    Frida requires matching major.minor versions for full compatibility.
    
    Args:
        v1: First version
        v2: Second version
        strict: If True, requires exact match
        
    Returns:
        True if compatible
    """
    p1 = parse_version(v1)
    p2 = parse_version(v2)
    
    if strict:
        return p1 == p2
    
    # Major and minor must match for Frida compatibility
    return p1[0] == p2[0] and p1[1] == p2[1]


def get_android_codename(version: int) -> str:
    """Get Android codename from version number."""
    codenames = {
        5: "Lollipop",
        6: "Marshmallow", 
        7: "Nougat",
        8: "Oreo",
        9: "Pie",
        10: "Q",
        11: "R",
        12: "S",
        13: "Tiramisu",
        14: "Upside Down Cake",
        15: "Vanilla Ice Cream",
    }
    return codenames.get(version, "Unknown")


class VersionChecker:
    """
    Checks and manages version compatibility between Frida components.
    """
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.adb = ADBClient(device_serial=device_serial) if device_serial else None
        self.fm = FridaManager(device_serial=device_serial) if device_serial else None
    
    def get_frida_client_version(self) -> VersionInfo:
        """Get Frida Python library version on host."""
        try:
            import frida
            return VersionInfo(
                component="Frida Python",
                version=frida.__version__,
                installed=True
            )
        except ImportError:
            return VersionInfo(
                component="Frida Python",
                version=None,
                installed=False
            )
    
    def get_frida_tools_version(self) -> VersionInfo:
        """Get frida-tools version on host."""
        try:
            result = subprocess.run(
                ["frida", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return VersionInfo(
                    component="Frida Tools",
                    version=version,
                    installed=True
                )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        # Try via pip
        try:
            result = subprocess.run(
                ["pip", "show", "frida-tools"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                        return VersionInfo(
                            component="Frida Tools",
                            version=version,
                            installed=True
                        )
        except subprocess.SubprocessError:
            pass
        
        return VersionInfo(
            component="Frida Tools",
            version=None,
            installed=False
        )
    
    def get_frida_server_version(self) -> VersionInfo:
        """Get Frida server version on device."""
        if not self.fm:
            return VersionInfo(
                component="Frida Server",
                version=None,
                installed=False
            )
        
        # Check running server first
        servers = self.fm.get_running_servers()
        if servers and servers[0].path:
            # Extract version from path
            path = servers[0].path
            match = re.search(r'frida-server-(\d+\.\d+\.\d+)', path)
            if match:
                return VersionInfo(
                    component="Frida Server",
                    version=match.group(1),
                    installed=True
                )
        
        # Check installed servers
        installed = self.fm.list_installed_servers()
        if installed:
            # Get version from first installed server
            match = re.search(r'frida-server-(\d+\.\d+\.\d+)', installed[0])
            if match:
                return VersionInfo(
                    component="Frida Server",
                    version=match.group(1),
                    installed=True
                )
        
        return VersionInfo(
            component="Frida Server",
            version=None,
            installed=False
        )
    
    def get_device_info(self) -> Optional[Dict]:
        """Get comprehensive device information."""
        if not self.adb:
            return None
        
        info = {}
        
        # Android version
        version_str = self.adb.get_property("ro.build.version.release")
        try:
            info["android_version"] = int(version_str.split(".")[0]) if version_str else 0
        except (ValueError, AttributeError):
            info["android_version"] = 0
        
        # SDK version
        sdk = self.adb.get_property("ro.build.version.sdk")
        info["sdk_version"] = int(sdk) if sdk and sdk.isdigit() else 0
        
        # Architecture
        arch = self.adb.get_property("ro.product.cpu.abi")
        info["architecture"] = arch or "unknown"
        
        # Frida architecture mapping
        arch_map = {
            "arm64-v8a": "arm64",
            "arm64": "arm64",
            "armeabi-v7a": "arm",
            "armeabi": "arm",
            "x86": "x86",
            "x86_64": "x86_64",
        }
        info["frida_arch"] = arch_map.get(arch, "unknown")
        
        # Build info
        info["build_id"] = self.adb.get_property("ro.build.id")
        info["build_fingerprint"] = self.adb.get_property("ro.build.fingerprint")
        info["device_model"] = self.adb.get_property("ro.product.model")
        info["manufacturer"] = self.adb.get_property("ro.product.manufacturer")
        info["security_patch"] = self.adb.get_property("ro.build.version.security_patch")
        
        return info
    
    def check_compatibility(self) -> CompatibilityResult:
        """
        Check version compatibility between all Frida components.
        
        Returns:
            CompatibilityResult with status and recommendations
        """
        client = self.get_frida_client_version()
        tools = self.get_frida_tools_version()
        server = self.get_frida_server_version()
        
        # Check if components are installed
        if not client.installed:
            return CompatibilityResult(
                status=VersionStatus.NOT_INSTALLED,
                message="Frida Python library not installed on host",
                server_version=server.version,
                client_version=None,
                tools_version=tools.version,
                fix_command="pip install frida"
            )
        
        if not server.installed:
            return CompatibilityResult(
                status=VersionStatus.NOT_INSTALLED,
                message="Frida server not installed on device",
                server_version=None,
                client_version=client.version,
                tools_version=tools.version,
                fix_command=f"f4f install {client.version}" if client.version else "f4f install --latest"
            )
        
        # Check client-server compatibility
        if client.version and server.version:
            if versions_compatible(client.version, server.version, strict=True):
                status = VersionStatus.MATCH
                message = f"Perfect match: Client {client.version} = Server {server.version}"
            elif versions_compatible(client.version, server.version, strict=False):
                status = VersionStatus.COMPATIBLE
                message = f"Compatible: Client {client.version} ~ Server {server.version}"
            else:
                status = VersionStatus.MISMATCH
                message = f"Version mismatch: Client {client.version} ≠ Server {server.version}"
                
                return CompatibilityResult(
                    status=status,
                    message=message,
                    server_version=server.version,
                    client_version=client.version,
                    tools_version=tools.version,
                    fix_command=f"f4f install {client.version}"
                )
        else:
            status = VersionStatus.UNKNOWN
            message = "Could not determine versions"
        
        return CompatibilityResult(
            status=status,
            message=message,
            server_version=server.version,
            client_version=client.version,
            tools_version=tools.version
        )
    
    def get_recommended_version(self) -> Optional[DeviceRecommendation]:
        """
        Get recommended Frida version based on device information.
        
        Returns:
            DeviceRecommendation or None
        """
        device_info = self.get_device_info()
        if not device_info:
            return None
        
        android_version = device_info["android_version"]
        
        # Get recommendation from mapping
        rec = ANDROID_FRIDA_RECOMMENDATIONS.get(android_version, {
            "min": "12.0.0",
            "recommended": get_latest_frida_version() or "16.1.17"
        })
        
        # Get current server version
        server = self.get_frida_server_version()
        
        # Build notes
        notes = []
        
        if android_version >= 14:
            notes.append("Android 14+ may require latest Frida for full compatibility")
        
        if "x86" in device_info["architecture"]:
            notes.append("x86 device detected - likely an emulator")
        
        if device_info.get("security_patch"):
            notes.append(f"Security patch: {device_info['security_patch']}")
        
        return DeviceRecommendation(
            android_version=android_version,
            android_codename=get_android_codename(android_version),
            sdk_version=device_info["sdk_version"],
            architecture=device_info["frida_arch"],
            min_frida_version=rec["min"],
            recommended_frida_version=rec["recommended"],
            current_server_version=server.version if server.installed else None,
            notes=notes
        )
    
    def get_all_versions(self) -> Dict[str, VersionInfo]:
        """Get all version information."""
        return {
            "client": self.get_frida_client_version(),
            "tools": self.get_frida_tools_version(),
            "server": self.get_frida_server_version(),
        }
    
    def fix_version_mismatch(self, target_version: Optional[str] = None) -> Tuple[bool, str]:
        """
        Fix version mismatch by installing matching server version.
        
        Args:
            target_version: Target version (default: match client version)
            
        Returns:
            Tuple of (success, message)
        """
        if not target_version:
            client = self.get_frida_client_version()
            if not client.installed or not client.version:
                return False, "Cannot determine target version - Frida client not installed"
            target_version = client.version
        
        if not self.fm:
            return False, "No device connected"
        
        # Get device architecture
        device_info = self.get_device_info()
        if not device_info:
            return False, "Cannot get device information"
        
        arch = device_info["frida_arch"]
        if arch == "unknown":
            return False, "Unknown device architecture"
        
        # Install matching version
        logger.info(f"Installing Frida server {target_version} for {arch}")
        server_path = self.fm.install_server(target_version, arch, force=True)
        
        if server_path:
            return True, f"Installed Frida server {target_version}"
        else:
            return False, "Failed to install Frida server"


class Automator:
    """
    Automates Frida setup based on device information.
    """
    
    def __init__(self, device_serial: str):
        self.device_serial = device_serial
        self.checker = VersionChecker(device_serial=device_serial)
        self.fm = FridaManager(device_serial=device_serial)
        self.adb = ADBClient(device_serial=device_serial)
    
    def get_target_version(self) -> Tuple[str, str]:
        """
        Determine the target Frida version to install.
        
        Priority:
        1. Match host's Frida client version (for compatibility)
        2. Use recommended version for Android version
        3. Fall back to latest
        
        Returns:
            Tuple of (version, reason)
        """
        # Check host's Frida client version first
        client = self.checker.get_frida_client_version()
        if client.installed and client.version:
            return client.version, f"Matching host Frida client v{client.version}"
        
        # Fall back to device recommendation
        rec = self.checker.get_recommended_version()
        if rec and rec.recommended_frida_version:
            return rec.recommended_frida_version, f"Recommended for Android {rec.android_version}"
        
        # Last resort: latest
        latest = get_latest_frida_version()
        if latest:
            return latest, "Latest available version"
        
        return "16.1.17", "Default fallback version"
    
    def analyze(self) -> Dict:
        """
        Analyze device and current setup.
        
        Returns:
            Analysis results
        """
        results = {
            "device": self.checker.get_device_info(),
            "versions": self.checker.get_all_versions(),
            "compatibility": self.checker.check_compatibility(),
            "recommendation": self.checker.get_recommended_version(),
            "server_status": self.fm.get_server_status(),
            "issues": [],
            "actions": [],
            "target_version": None,
            "target_reason": None,
        }
        
        # Determine target version for installation/fix
        target_version, target_reason = self.get_target_version()
        results["target_version"] = target_version
        results["target_reason"] = target_reason
        
        # Analyze issues and needed actions
        compat = results["compatibility"]
        client = results["versions"]["client"]
        server = results["versions"]["server"]
        
        if not client.installed:
            results["issues"].append("Frida Python library not installed on host")
            results["actions"].append({
                "action": "install_frida_client",
                "command": "pip install frida frida-tools",
                "description": "Install Frida client and tools"
            })
        
        if not server.installed:
            results["issues"].append("Frida server not installed on device")
            results["actions"].append({
                "action": "install_frida_server",
                "version": target_version,
                "command": f"f4f install {target_version}",
                "description": f"Install Frida server {target_version} ({target_reason})"
            })
        elif compat.status == VersionStatus.MISMATCH:
            # Version mismatch - install matching version
            if client.installed and client.version:
                fix_version = client.version
                fix_reason = f"Match host client v{client.version}"
            else:
                fix_version = target_version
                fix_reason = target_reason
            
            results["issues"].append(f"Version mismatch: {compat.message}")
            results["actions"].append({
                "action": "fix_version",
                "version": fix_version,
                "command": f"f4f install {fix_version}",
                "description": f"Install Frida server {fix_version} ({fix_reason})"
            })
        
        if not results["server_status"]["running"] and results["versions"]["server"].installed:
            results["actions"].append({
                "action": "start_server",
                "command": "f4f start",
                "description": "Start Frida server"
            })
        
        # Check SELinux
        stdout, _, _ = self.adb.shell("getenforce")
        if "Enforcing" in stdout:
            results["issues"].append("SELinux is Enforcing (may block Frida)")
            results["actions"].append({
                "action": "disable_selinux",
                "command": "adb shell su -c 'setenforce 0'",
                "description": "Set SELinux to Permissive"
            })
        
        return results
    
    def run(self, fix_issues: bool = True) -> Dict:
        """
        Run automated setup.
        
        Args:
            fix_issues: Automatically fix detected issues
            
        Returns:
            Results of automation
        """
        analysis = self.analyze()
        results = {
            "analysis": analysis,
            "actions_taken": [],
            "success": True,
            "final_status": None,
        }
        
        if not fix_issues:
            return results
        
        # Execute actions
        for action in analysis["actions"]:
            action_type = action["action"]
            success = False
            message = ""
            
            try:
                if action_type == "install_frida_server":
                    # Use version from action (already calculated for compatibility)
                    version = action.get("version") or analysis.get("target_version")
                    if version:
                        arch = analysis["device"]["frida_arch"]
                        logger.info(f"Installing Frida server {version} to match host client")
                        path = self.fm.install_server(version, arch, force=True)
                        success = path is not None
                        message = f"Installed v{version} (matches host)" if success else "Installation failed"
                    else:
                        message = "Could not determine version to install"
                
                elif action_type == "fix_version":
                    # Get version from action or use client version
                    version = action.get("version")
                    if version:
                        arch = analysis["device"]["frida_arch"]
                        logger.info(f"Fixing version mismatch: installing {version}")
                        path = self.fm.install_server(version, arch, force=True)
                        success = path is not None
                        message = f"Installed v{version} (matches host)" if success else "Installation failed"
                    else:
                        success, message = self.checker.fix_version_mismatch()
                
                elif action_type == "start_server":
                    installed = self.fm.list_installed_servers()
                    if installed:
                        success, _ = self.fm.start_server(installed[0])
                        message = "Server started" if success else "Failed to start"
                    else:
                        message = "No server to start"
                
                elif action_type == "disable_selinux":
                    self.adb.shell_su("setenforce 0")
                    success = True
                    message = "SELinux set to Permissive"
                
                elif action_type == "install_frida_client":
                    # Can't do this automatically - user needs to run pip
                    success = False
                    message = "Run manually: pip install frida frida-tools"
                
            except Exception as e:
                success = False
                message = str(e)
            
            results["actions_taken"].append({
                **action,
                "success": success,
                "message": message,
            })
            
            if not success and action_type in ["install_frida_server", "fix_version"]:
                results["success"] = False
        
        # Get final status
        results["final_status"] = self.fm.get_server_status()
        
        return results
