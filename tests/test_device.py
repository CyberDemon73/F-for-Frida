"""
Tests for Device Manager module
"""

import pytest
from unittest.mock import patch, MagicMock
from f_for_frida.core.device import DeviceManager, DeviceInfo, ARCHITECTURE_MAP


class TestArchitectureMap:
    """Tests for architecture mapping"""
    
    def test_arm64_mapping(self):
        """Test ARM64 architecture mappings"""
        assert ARCHITECTURE_MAP["arm64-v8a"] == "arm64"
        assert ARCHITECTURE_MAP["arm64"] == "arm64"
    
    def test_arm_mapping(self):
        """Test ARM architecture mappings"""
        assert ARCHITECTURE_MAP["armeabi-v7a"] == "arm"
        assert ARCHITECTURE_MAP["armeabi"] == "arm"
    
    def test_x86_mapping(self):
        """Test x86 architecture mappings"""
        assert ARCHITECTURE_MAP["x86"] == "x86"
        assert ARCHITECTURE_MAP["x86_64"] == "x86_64"


class TestDeviceInfo:
    """Tests for DeviceInfo dataclass"""
    
    def test_device_info_creation(self):
        """Test DeviceInfo creation"""
        info = DeviceInfo(
            serial="ABC123",
            model="Pixel",
            manufacturer="Google",
            android_version="13",
            sdk_version="33",
            architecture="arm64-v8a",
            frida_architecture="arm64",
            is_rooted=True,
            status="device"
        )
        
        assert info.serial == "ABC123"
        assert info.model == "Pixel"
        assert info.is_rooted is True
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        info = DeviceInfo(
            serial="ABC123",
            model="Pixel",
            manufacturer="Google",
            android_version="13",
            sdk_version="33",
            architecture="arm64-v8a",
            frida_architecture="arm64",
            is_rooted=True,
            status="device"
        )
        
        d = info.to_dict()
        assert d["serial"] == "ABC123"
        assert d["model"] == "Pixel"
        assert d["is_rooted"] is True


class TestDeviceManager:
    """Tests for DeviceManager class"""
    
    def test_init(self):
        """Test DeviceManager initialization"""
        dm = DeviceManager()
        assert dm._devices_cache == {}
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_get_connected_devices(self, mock_list):
        """Test getting connected devices"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device"),
            Device(serial="DEF456", status="unauthorized"),
        ]
        
        dm = DeviceManager()
        devices = dm.get_connected_devices()
        
        assert len(devices) == 2
        mock_list.assert_called_once()
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_get_authorized_devices(self, mock_list):
        """Test getting only authorized devices"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device"),
            Device(serial="DEF456", status="unauthorized"),
            Device(serial="GHI789", status="device"),
        ]
        
        dm = DeviceManager()
        devices = dm.get_authorized_devices()
        
        assert len(devices) == 2
        assert all(d.is_authorized for d in devices)
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_select_device_single(self, mock_list):
        """Test device selection with single device"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device"),
        ]
        
        dm = DeviceManager()
        serial = dm.select_device()
        
        assert serial == "ABC123"
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_select_device_multiple_no_serial(self, mock_list):
        """Test device selection with multiple devices and no serial specified"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device"),
            Device(serial="DEF456", status="device"),
        ]
        
        dm = DeviceManager()
        serial = dm.select_device()
        
        # Should return None when multiple devices and no serial specified
        assert serial is None
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_select_device_with_serial(self, mock_list):
        """Test device selection with specific serial"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device"),
            Device(serial="DEF456", status="device"),
        ]
        
        dm = DeviceManager()
        serial = dm.select_device("DEF456")
        
        assert serial == "DEF456"
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_select_device_invalid_serial(self, mock_list):
        """Test device selection with invalid serial"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device"),
        ]
        
        dm = DeviceManager()
        serial = dm.select_device("INVALID")
        
        assert serial is None
    
    @patch('f_for_frida.core.device.ADBClient.list_devices')
    def test_select_device_no_devices(self, mock_list):
        """Test device selection with no devices"""
        mock_list.return_value = []
        
        dm = DeviceManager()
        serial = dm.select_device()
        
        assert serial is None
