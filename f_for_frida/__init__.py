"""
F-for-Frida - Automated Frida Server Management for Android Devices
"""

__version__ = "2.0.0"
__author__ = "Mohamed Hisham Sharaf"
__license__ = "MIT"

from .core.device import DeviceManager
from .core.frida_manager import FridaManager
from .core.adb import ADBClient

__all__ = ["DeviceManager", "FridaManager", "ADBClient", "__version__"]
