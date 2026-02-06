"""
Device Manager - Handles device detection and management
"""

from typing import Optional, List, Dict
from dataclasses import dataclass, field

from .adb import ADBClient, Device
from ..utils.logger import get_logger

logger = get_logger(__name__)


# Architecture mapping from Android ABI to Frida format
ARCHITECTURE_MAP = {
    "arm64-v8a": "arm64",
    "arm64": "arm64",
    "armeabi-v7a": "arm",
    "armeabi": "arm",
    "x86": "x86",
    "x86_64": "x86_64",
}


@dataclass
class DeviceInfo:
    """Complete device information"""
    serial: str
    model: str
    manufacturer: str
    android_version: str
    sdk_version: str
    architecture: str
    frida_architecture: str
    is_rooted: bool
    status: str
    
    def to_dict(self) -> Dict:
        return {
            "serial": self.serial,
            "model": self.model,
            "manufacturer": self.manufacturer,
            "android_version": self.android_version,
            "sdk_version": self.sdk_version,
            "architecture": self.architecture,
            "frida_architecture": self.frida_architecture,
            "is_rooted": self.is_rooted,
            "status": self.status,
        }


class DeviceManager:
    """
    Manages Android device connections and provides device information.
    Supports multiple connected devices.
    """
    
    def __init__(self):
        self._devices_cache: Dict[str, DeviceInfo] = {}
    
    @staticmethod
    def get_connected_devices() -> List[Device]:
        """
        Get list of all connected devices.
        
        Returns:
            List of Device objects
        """
        return ADBClient.list_devices()
    
    @staticmethod
    def get_authorized_devices() -> List[Device]:
        """
        Get list of authorized (ready to use) devices.
        
        Returns:
            List of authorized Device objects
        """
        return [d for d in ADBClient.list_devices() if d.is_authorized]
    
    def get_device_info(self, serial: str) -> Optional[DeviceInfo]:
        """
        Get detailed information about a specific device.
        
        Args:
            serial: Device serial number
            
        Returns:
            DeviceInfo object or None if device not found
        """
        adb = ADBClient(device_serial=serial)
        
        # Get device properties
        model = adb.get_property("ro.product.model") or "Unknown"
        manufacturer = adb.get_property("ro.product.manufacturer") or "Unknown"
        android_version = adb.get_property("ro.build.version.release") or "Unknown"
        sdk_version = adb.get_property("ro.build.version.sdk") or "Unknown"
        arch = adb.get_property("ro.product.cpu.abi") or "Unknown"
        
        # Map to Frida architecture
        frida_arch = ARCHITECTURE_MAP.get(arch, "unknown")
        
        # Check root status
        is_rooted = adb.check_root()
        
        # Get device status
        devices = ADBClient.list_devices()
        status = "disconnected"
        for d in devices:
            if d.serial == serial:
                status = d.status
                break
        
        info = DeviceInfo(
            serial=serial,
            model=model,
            manufacturer=manufacturer,
            android_version=android_version,
            sdk_version=sdk_version,
            architecture=arch,
            frida_architecture=frida_arch,
            is_rooted=is_rooted,
            status=status,
        )
        
        self._devices_cache[serial] = info
        return info
    
    def get_all_device_info(self) -> List[DeviceInfo]:
        """
        Get detailed information about all connected devices.
        
        Returns:
            List of DeviceInfo objects
        """
        devices = self.get_authorized_devices()
        return [self.get_device_info(d.serial) for d in devices]
    
    def select_device(self, serial: Optional[str] = None) -> Optional[str]:
        """
        Select a device for operations.
        
        Args:
            serial: Device serial. If None and only one device connected, selects it.
            
        Returns:
            Selected device serial or None
        """
        devices = self.get_authorized_devices()
        
        if not devices:
            logger.error("No authorized devices connected")
            return None
        
        if serial:
            # Check if specified device exists
            for d in devices:
                if d.serial == serial:
                    return serial
            logger.error(f"Device {serial} not found")
            return None
        
        if len(devices) == 1:
            return devices[0].serial
        
        # Multiple devices - need explicit selection
        logger.warning(f"Multiple devices connected. Please specify device serial.")
        return None
    
    def wait_for_device(self, serial: Optional[str] = None, timeout: int = 30) -> bool:
        """
        Wait for a device to be connected and authorized.
        
        Args:
            serial: Specific device serial to wait for
            timeout: Timeout in seconds
            
        Returns:
            True if device is ready, False if timeout
        """
        import time
        start = time.time()
        
        while time.time() - start < timeout:
            devices = self.get_authorized_devices()
            
            if serial:
                if any(d.serial == serial for d in devices):
                    return True
            elif devices:
                return True
            
            time.sleep(1)
        
        return False
