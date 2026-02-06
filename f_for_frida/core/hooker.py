"""
Application Hooking Helper for F-for-Frida
Simplified interface for hooking Android applications with Frida
"""

import subprocess
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .adb import ADBClient
from .frida_manager import FridaManager
from .scripts import ScriptManager, BUILTIN_SCRIPTS
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HookMode(Enum):
    """Frida hook mode"""
    ATTACH = "attach"  # Attach to running process
    SPAWN = "spawn"    # Spawn new process


@dataclass
class AppInfo:
    """Android application information"""
    package_name: str
    name: Optional[str] = None
    version: Optional[str] = None
    pid: Optional[int] = None
    is_running: bool = False
    is_debuggable: bool = False


class AppHooker:
    """
    Simplified interface for hooking Android applications.
    Handles app enumeration, process management, and script injection.
    """
    
    def __init__(self, device_serial: Optional[str] = None):
        self.device_serial = device_serial
        self.adb = ADBClient(device_serial=device_serial)
        self.fm = FridaManager(device_serial=device_serial)
        self.script_manager = ScriptManager()
    
    def list_packages(self, filter_term: Optional[str] = None, third_party_only: bool = True) -> List[str]:
        """
        List installed packages on device.
        
        Args:
            filter_term: Filter packages containing this term
            third_party_only: Only show third-party apps (not system)
            
        Returns:
            List of package names
        """
        cmd = "pm list packages"
        if third_party_only:
            cmd += " -3"
        
        stdout, stderr, rc = self.adb.shell(cmd)
        
        if rc != 0:
            logger.error(f"Failed to list packages: {stderr}")
            return []
        
        packages = []
        for line in stdout.splitlines():
            if line.startswith("package:"):
                pkg = line[8:].strip()
                if filter_term is None or filter_term.lower() in pkg.lower():
                    packages.append(pkg)
        
        return sorted(packages)
    
    def get_app_info(self, package_name: str) -> Optional[AppInfo]:
        """
        Get detailed information about an application.
        
        Args:
            package_name: Package name (e.g., com.example.app)
            
        Returns:
            AppInfo object or None if not found
        """
        # Check if package exists
        stdout, stderr, rc = self.adb.shell(f"pm path {package_name}")
        if rc != 0 or not stdout:
            return None
        
        # Get app info from dumpsys
        info = AppInfo(package_name=package_name)
        
        # Get version
        stdout, stderr, rc = self.adb.shell(f"dumpsys package {package_name} | grep versionName")
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                if "versionName=" in line:
                    info.version = line.split("=")[1].strip()
                    break
        
        # Check if debuggable
        stdout, stderr, rc = self.adb.shell(f"run-as {package_name} id 2>/dev/null")
        info.is_debuggable = rc == 0
        
        # Check if running and get PID
        pid = self.get_app_pid(package_name)
        if pid:
            info.pid = pid
            info.is_running = True
        
        return info
    
    def get_app_pid(self, package_name: str) -> Optional[int]:
        """
        Get PID of a running application.
        
        Args:
            package_name: Package name
            
        Returns:
            PID or None if not running
        """
        stdout, stderr, rc = self.adb.shell(f"pidof {package_name}")
        if rc == 0 and stdout:
            try:
                return int(stdout.strip().split()[0])
            except (ValueError, IndexError):
                pass
        
        # Fallback to ps
        stdout, stderr, rc = self.adb.shell(f"ps -A | grep {package_name}")
        if rc == 0 and stdout:
            for line in stdout.splitlines():
                if package_name in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            return int(parts[1])
                        except ValueError:
                            continue
        
        return None
    
    def get_running_apps(self) -> List[AppInfo]:
        """
        Get list of currently running applications.
        
        Returns:
            List of AppInfo objects
        """
        apps = []
        
        stdout, stderr, rc = self.adb.shell("ps -A | grep -E 'com\\.|org\\.'")
        if rc != 0:
            return apps
        
        seen = set()
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 9:
                pkg = parts[-1]
                if pkg not in seen and not pkg.startswith('['):
                    seen.add(pkg)
                    try:
                        pid = int(parts[1])
                        apps.append(AppInfo(
                            package_name=pkg,
                            pid=pid,
                            is_running=True
                        ))
                    except (ValueError, IndexError):
                        continue
        
        return apps
    
    def start_app(self, package_name: str) -> bool:
        """
        Start an application.
        
        Args:
            package_name: Package name
            
        Returns:
            True if successful
        """
        # Get main activity
        stdout, stderr, rc = self.adb.shell(
            f"cmd package resolve-activity --brief {package_name} | tail -1"
        )
        
        if rc == 0 and stdout and "/" in stdout:
            activity = stdout.strip()
        else:
            # Fallback to monkey
            stdout, stderr, rc = self.adb.shell(
                f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
            )
            return rc == 0
        
        # Start activity
        stdout, stderr, rc = self.adb.shell(f"am start -n {activity}")
        return rc == 0 or "Starting" in stdout
    
    def stop_app(self, package_name: str) -> bool:
        """
        Force stop an application.
        
        Args:
            package_name: Package name
            
        Returns:
            True if successful
        """
        stdout, stderr, rc = self.adb.shell(f"am force-stop {package_name}")
        return rc == 0
    
    def ensure_frida_running(self) -> bool:
        """Ensure Frida server is running on device."""
        if self.fm.is_server_running():
            return True
        
        # Try to start
        installed = self.fm.list_installed_servers()
        if not installed:
            logger.error("No Frida server installed")
            return False
        
        success, _ = self.fm.start_server(installed[0])
        return success
    
    def hook_app(
        self,
        package_name: str,
        script: Optional[str] = None,
        script_name: Optional[str] = None,
        mode: HookMode = HookMode.ATTACH,
        pause_on_spawn: bool = False
    ) -> Tuple[bool, str]:
        """
        Hook an application with Frida.
        
        Args:
            package_name: Target package name
            script: Frida script content
            script_name: Name of built-in script to use
            mode: ATTACH to running or SPAWN new process
            pause_on_spawn: Pause app after spawn (for early instrumentation)
            
        Returns:
            Tuple of (success, message/command)
        """
        # Ensure Frida is running
        if not self.ensure_frida_running():
            return False, "Failed to start Frida server"
        
        # Get script content
        if script_name:
            builtin = self.script_manager.get_builtin(script_name)
            if builtin:
                script = builtin.content
            else:
                custom = self.script_manager.get_custom(script_name)
                if custom:
                    script = custom
                else:
                    return False, f"Script '{script_name}' not found"
        
        # Build frida command
        if mode == HookMode.SPAWN:
            cmd = f"frida -U -f {package_name}"
            if pause_on_spawn:
                cmd += " --pause"
        else:
            # Check if app is running
            pid = self.get_app_pid(package_name)
            if not pid:
                return False, f"App {package_name} is not running. Use spawn mode or start the app first."
            cmd = f"frida -U -p {pid}"
        
        # Add device serial if specified
        if self.device_serial:
            cmd = cmd.replace("-U", f"-D {self.device_serial}")
        
        # Add script if provided
        if script:
            # Save script to temp file
            script_path = self.script_manager.save_script("_temp_hook", script)
            cmd += f" -l {script_path}"
        
        return True, cmd
    
    def quick_bypass(
        self,
        package_name: str,
        ssl_bypass: bool = True,
        root_bypass: bool = True,
        debug_bypass: bool = False,
        mode: HookMode = HookMode.SPAWN
    ) -> Tuple[bool, str]:
        """
        Quick setup for common bypass scenarios.
        
        Args:
            package_name: Target package
            ssl_bypass: Enable SSL pinning bypass
            root_bypass: Enable root detection bypass
            debug_bypass: Enable anti-debug bypass
            mode: Hook mode
            
        Returns:
            Tuple of (success, command)
        """
        scripts = []
        
        if ssl_bypass:
            scripts.append(BUILTIN_SCRIPTS["ssl-pinning-bypass"].content)
        if root_bypass:
            scripts.append(BUILTIN_SCRIPTS["root-detection-bypass"].content)
        if debug_bypass:
            scripts.append(BUILTIN_SCRIPTS["anti-debug-bypass"].content)
        
        if not scripts:
            return False, "No bypass options selected"
        
        # Combine scripts
        combined = "\n\n// === Combined Bypass Script ===\n\n".join(scripts)
        
        return self.hook_app(package_name, script=combined, mode=mode)
    
    def generate_hook_command(
        self,
        package_name: str,
        scripts: List[str] = None,
        spawn: bool = False,
        no_pause: bool = True
    ) -> str:
        """
        Generate a Frida command for manual execution.
        
        Args:
            package_name: Target package
            scripts: List of script names to include
            spawn: Use spawn mode
            no_pause: Don't pause on spawn
            
        Returns:
            Command string
        """
        if spawn:
            cmd = f"frida -U -f {package_name}"
            if no_pause:
                cmd += " --no-pause"
        else:
            cmd = f"frida -U -n {package_name}"
        
        if self.device_serial:
            cmd = cmd.replace("-U", f"-D {self.device_serial}")
        
        if scripts:
            for script_name in scripts:
                # Export scripts if they're built-in
                builtin = self.script_manager.get_builtin(script_name)
                if builtin:
                    path = self.script_manager.export_builtin(script_name)
                    if path:
                        cmd += f" -l {path}"
        
        return cmd
