"""
Tests for Doctor module
"""

import pytest
from unittest.mock import patch, MagicMock
from f_for_frida.core.doctor import Doctor, CheckResult, CheckStatus


class TestCheckStatus:
    """Tests for CheckStatus enum"""
    
    def test_values(self):
        """Test CheckStatus values"""
        assert CheckStatus.OK.value == "ok"
        assert CheckStatus.WARNING.value == "warning"
        assert CheckStatus.ERROR.value == "error"
        assert CheckStatus.SKIPPED.value == "skipped"


class TestCheckResult:
    """Tests for CheckResult dataclass"""
    
    def test_creation(self):
        """Test CheckResult creation"""
        result = CheckResult(
            name="Test Check",
            status=CheckStatus.OK,
            message="All good"
        )
        
        assert result.name == "Test Check"
        assert result.status == CheckStatus.OK
        assert result.message == "All good"
        assert result.fix is None
    
    def test_with_fix(self):
        """Test CheckResult with fix suggestion"""
        result = CheckResult(
            name="Test Check",
            status=CheckStatus.ERROR,
            message="Something wrong",
            fix="Do this to fix"
        )
        
        assert result.fix == "Do this to fix"
    
    def test_icons(self):
        """Test icon property"""
        ok = CheckResult("Test", CheckStatus.OK, "msg")
        warning = CheckResult("Test", CheckStatus.WARNING, "msg")
        error = CheckResult("Test", CheckStatus.ERROR, "msg")
        skipped = CheckResult("Test", CheckStatus.SKIPPED, "msg")
        
        assert ok.icon == "✓"
        assert warning.icon == "!"
        assert error.icon == "✗"
        assert skipped.icon == "○"


class TestDoctor:
    """Tests for Doctor class"""
    
    def test_init(self):
        """Test Doctor initialization"""
        doc = Doctor()
        assert doc.device_serial is None
        assert doc.results == []
    
    def test_init_with_device(self):
        """Test Doctor with device serial"""
        doc = Doctor(device_serial="ABC123")
        assert doc.device_serial == "ABC123"
    
    def test_check_python_version(self):
        """Test Python version check"""
        doc = Doctor()
        result = doc.check_python_version()
        
        # Should pass since we're running on Python 3.8+
        assert result.status == CheckStatus.OK
        assert "Python" in result.message
    
    @patch('shutil.which')
    def test_check_adb_installed_true(self, mock_which):
        """Test ADB check when installed"""
        mock_which.return_value = "/usr/bin/adb"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Android Debug Bridge version 1.0.41",
                stderr="",
                returncode=0
            )
            
            doc = Doctor()
            result = doc.check_adb_installed()
            
            assert result.status == CheckStatus.OK
    
    @patch('shutil.which')
    def test_check_adb_installed_false(self, mock_which):
        """Test ADB check when not installed"""
        mock_which.return_value = None
        
        doc = Doctor()
        result = doc.check_adb_installed()
        
        assert result.status == CheckStatus.ERROR
        assert result.fix is not None
    
    @patch('shutil.which')
    def test_check_xz_installed_true(self, mock_which):
        """Test XZ check when installed"""
        mock_which.return_value = "/usr/bin/xz"
        
        doc = Doctor()
        result = doc.check_xz_installed()
        
        assert result.status == CheckStatus.OK
    
    @patch('shutil.which')
    def test_check_xz_installed_false(self, mock_which):
        """Test XZ check when not installed"""
        mock_which.return_value = None
        
        doc = Doctor()
        result = doc.check_xz_installed()
        
        assert result.status == CheckStatus.ERROR
    
    @patch('f_for_frida.core.doctor.ADBClient.list_devices')
    def test_check_device_connected_yes(self, mock_list):
        """Test device check when connected"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="device")
        ]
        
        doc = Doctor()
        result = doc.check_device_connected()
        
        assert result.status == CheckStatus.OK
    
    @patch('f_for_frida.core.doctor.ADBClient.list_devices')
    def test_check_device_connected_no(self, mock_list):
        """Test device check when not connected"""
        mock_list.return_value = []
        
        doc = Doctor()
        result = doc.check_device_connected()
        
        assert result.status == CheckStatus.ERROR
    
    @patch('f_for_frida.core.doctor.ADBClient.list_devices')
    def test_check_device_unauthorized(self, mock_list):
        """Test device check when unauthorized"""
        from f_for_frida.core.adb import Device
        
        mock_list.return_value = [
            Device(serial="ABC123", status="unauthorized")
        ]
        
        doc = Doctor()
        result = doc.check_device_connected()
        
        assert result.status == CheckStatus.WARNING
    
    def test_get_summary(self):
        """Test summary generation"""
        doc = Doctor()
        doc.results = [
            CheckResult("A", CheckStatus.OK, "ok"),
            CheckResult("B", CheckStatus.OK, "ok"),
            CheckResult("C", CheckStatus.WARNING, "warn"),
            CheckResult("D", CheckStatus.ERROR, "error"),
            CheckResult("E", CheckStatus.SKIPPED, "skip"),
        ]
        
        ok, warning, error, skipped = doc.get_summary()
        
        assert ok == 2
        assert warning == 1
        assert error == 1
        assert skipped == 1
    
    def test_has_errors(self):
        """Test has_errors method"""
        doc = Doctor()
        
        doc.results = [
            CheckResult("A", CheckStatus.OK, "ok"),
            CheckResult("B", CheckStatus.WARNING, "warn"),
        ]
        assert doc.has_errors() is False
        
        doc.results.append(CheckResult("C", CheckStatus.ERROR, "error"))
        assert doc.has_errors() is True
    
    def test_get_fixes(self):
        """Test getting fixes"""
        doc = Doctor()
        doc.results = [
            CheckResult("A", CheckStatus.OK, "ok"),
            CheckResult("B", CheckStatus.ERROR, "error", fix="Fix B"),
            CheckResult("C", CheckStatus.WARNING, "warn", fix="Fix C"),
            CheckResult("D", CheckStatus.ERROR, "error"),  # No fix
        ]
        
        fixes = doc.get_fixes()
        
        assert len(fixes) == 2
        assert ("B", "Fix B") in fixes
        assert ("C", "Fix C") in fixes
