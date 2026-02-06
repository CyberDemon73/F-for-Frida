"""
Tests for ADB Client module
"""

import pytest
from unittest.mock import patch, MagicMock
from f_for_frida.core.adb import ADBClient, Device


class TestDevice:
    """Tests for Device dataclass"""
    
    def test_device_creation(self):
        """Test basic device creation"""
        device = Device(serial="ABC123", status="device", model="Pixel")
        assert device.serial == "ABC123"
        assert device.status == "device"
        assert device.model == "Pixel"
    
    def test_is_authorized(self):
        """Test is_authorized property"""
        authorized = Device(serial="ABC123", status="device")
        unauthorized = Device(serial="ABC123", status="unauthorized")
        
        assert authorized.is_authorized is True
        assert unauthorized.is_authorized is False
    
    def test_is_unauthorized(self):
        """Test is_unauthorized property"""
        device = Device(serial="ABC123", status="unauthorized")
        assert device.is_unauthorized is True
    
    def test_str_representation(self):
        """Test string representation"""
        device = Device(serial="ABC123", status="device", model="Pixel")
        assert "ABC123" in str(device)
        assert "Pixel" in str(device)


class TestADBClient:
    """Tests for ADBClient class"""
    
    def test_init_without_serial(self):
        """Test initialization without device serial"""
        client = ADBClient()
        assert client.device_serial is None
    
    def test_init_with_serial(self):
        """Test initialization with device serial"""
        client = ADBClient(device_serial="ABC123")
        assert client.device_serial == "ABC123"
    
    def test_build_command_without_serial(self):
        """Test command building without serial"""
        client = ADBClient()
        cmd = client._build_adb_command(["devices"])
        assert cmd == ["adb", "devices"]
    
    def test_build_command_with_serial(self):
        """Test command building with serial"""
        client = ADBClient(device_serial="ABC123")
        cmd = client._build_adb_command(["shell", "ls"])
        assert cmd == ["adb", "-s", "ABC123", "shell", "ls"]
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution"""
        mock_run.return_value = MagicMock(
            stdout=b"output",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        stdout, stderr, rc = client.run_command(["devices"])
        
        assert stdout == "output"
        assert stderr == ""
        assert rc == 0
    
    @patch('subprocess.run')
    def test_run_command_timeout(self, mock_run):
        """Test command timeout handling"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=10)
        
        client = ADBClient()
        stdout, stderr, rc = client.run_command(["shell", "sleep", "100"], timeout=10)
        
        assert rc == -1
        assert "timeout" in stderr.lower()
    
    @patch('subprocess.run')
    def test_shell_command(self, mock_run):
        """Test shell command execution"""
        mock_run.return_value = MagicMock(
            stdout=b"result",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        stdout, stderr, rc = client.shell("ls /data")
        
        assert stdout == "result"
        assert rc == 0
    
    @patch('subprocess.run')
    def test_shell_su_command(self, mock_run):
        """Test shell command with su"""
        mock_run.return_value = MagicMock(
            stdout=b"uid=0(root)",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        stdout, stderr, rc = client.shell_su("id")
        
        # Verify su was used
        call_args = mock_run.call_args[0][0]
        assert "su" in call_args
    
    @patch('subprocess.run')
    def test_check_root_true(self, mock_run):
        """Test root check when device is rooted"""
        mock_run.return_value = MagicMock(
            stdout=b"uid=0(root) gid=0(root)",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        assert client.check_root() is True
    
    @patch('subprocess.run')
    def test_check_root_false(self, mock_run):
        """Test root check when device is not rooted"""
        mock_run.return_value = MagicMock(
            stdout=b"uid=1000(shell)",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        assert client.check_root() is False
    
    @patch('subprocess.run')
    def test_file_exists_true(self, mock_run):
        """Test file_exists when file exists"""
        mock_run.return_value = MagicMock(
            stdout=b"/data/local/tmp/frida-server",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        assert client.file_exists("/data/local/tmp/frida-server") is True
    
    @patch('subprocess.run')
    def test_file_exists_false(self, mock_run):
        """Test file_exists when file doesn't exist"""
        mock_run.return_value = MagicMock(
            stdout=b"",
            stderr=b"No such file or directory",
            returncode=1
        )
        
        client = ADBClient()
        assert client.file_exists("/nonexistent") is False
    
    @patch('subprocess.run')
    def test_list_devices(self, mock_run):
        """Test listing connected devices"""
        mock_run.return_value = MagicMock(
            stdout=b"List of devices attached\nABC123\tdevice model:Pixel\nDEF456\tunauthorized\n",
            stderr=b"",
            returncode=0
        )
        
        devices = ADBClient.list_devices()
        
        assert len(devices) == 2
        assert devices[0].serial == "ABC123"
        assert devices[0].status == "device"
        assert devices[0].model == "Pixel"
        assert devices[1].serial == "DEF456"
        assert devices[1].status == "unauthorized"
    
    @patch('subprocess.run')
    def test_list_devices_empty(self, mock_run):
        """Test listing devices when none connected"""
        mock_run.return_value = MagicMock(
            stdout=b"List of devices attached\n\n",
            stderr=b"",
            returncode=0
        )
        
        devices = ADBClient.list_devices()
        assert len(devices) == 0
    
    @patch('subprocess.run')
    def test_get_property(self, mock_run):
        """Test getting device property"""
        mock_run.return_value = MagicMock(
            stdout=b"arm64-v8a",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        prop = client.get_property("ro.product.cpu.abi")
        
        assert prop == "arm64-v8a"
    
    @patch('subprocess.run')
    def test_push_success(self, mock_run):
        """Test successful file push"""
        mock_run.return_value = MagicMock(
            stdout=b"1 file pushed",
            stderr=b"",
            returncode=0
        )
        
        client = ADBClient()
        result = client.push("/local/file", "/remote/file")
        
        assert result is True
    
    @patch('subprocess.run')
    def test_push_failure(self, mock_run):
        """Test failed file push"""
        mock_run.return_value = MagicMock(
            stdout=b"",
            stderr=b"error: device not found",
            returncode=1
        )
        
        client = ADBClient()
        result = client.push("/local/file", "/remote/file")
        
        assert result is False
