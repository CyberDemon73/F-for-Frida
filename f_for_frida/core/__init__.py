"""
Core modules for F-for-Frida
"""

from .adb import ADBClient
from .device import DeviceManager
from .frida_manager import FridaManager
from .wireless import WirelessADB
from .scripts import ScriptManager, FridaScript
from .doctor import Doctor, CheckResult, CheckStatus
from .hooker import AppHooker, AppInfo, HookMode
from .compatibility import (
    VersionChecker, 
    Automator,
    VersionStatus,
    VersionInfo,
    CompatibilityResult,
    DeviceRecommendation,
)

__all__ = [
    "ADBClient",
    "DeviceManager", 
    "FridaManager",
    "WirelessADB",
    "ScriptManager",
    "FridaScript",
    "Doctor",
    "CheckResult",
    "CheckStatus",
    "AppHooker",
    "AppInfo",
    "HookMode",
    "VersionChecker",
    "Automator",
    "VersionStatus",
    "VersionInfo",
    "CompatibilityResult",
    "DeviceRecommendation",
]
