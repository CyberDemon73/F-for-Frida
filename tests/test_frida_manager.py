"""
Tests for Frida Manager module
"""

import pytest
from unittest.mock import patch, MagicMock
from f_for_frida.core.frida_manager import FridaManager, FridaServerInfo


class TestFridaServerInfo:
    """Tests for FridaServerInfo dataclass"""
    
    def test_creation(self):
        """Test FridaServerInfo creation"""
        info = FridaServerInfo(pid=1234, path="/data/local/tmp/frida-server")
        
        assert info.pid == 1234
        assert info.path == "/data/local/tmp/frida-server"
        assert info.version is None
    
    def test_creation_with_version(self):
        """Test FridaServerInfo with version"""
        info = FridaServerInfo(pid=1234, path="/data/local/tmp/frida-server", version="16.1.17")
        
        assert info.version == "16.1.17"


class TestFridaManager:
    """Tests for FridaManager class"""
    
    def test_init(self):
        """Test FridaManager initialization"""
        fm = FridaManager()
        assert fm.device_serial is None
        assert fm.FRIDA_PORT == 27042
    
    def test_init_with_serial(self):
        """Test FridaManager with device serial"""
        fm = FridaManager(device_serial="ABC123")
        assert fm.device_serial == "ABC123"
    
    def test_server_path_template(self):
        """Test server path template"""
        fm = FridaManager()
        path = fm.FRIDA_PATH_TEMPLATE.format(version="16.1.17", arch="arm64")
        
        assert path == "/data/local/tmp/frida-server-16.1.17-android-arm64"
    
    @patch.object(FridaManager, 'get_running_servers')
    def test_is_server_running_true(self, mock_get):
        """Test is_server_running when servers are running"""
        mock_get.return_value = [FridaServerInfo(pid=1234, path="/data/local/tmp/frida")]
        
        fm = FridaManager()
        assert fm.is_server_running() is True
    
    @patch.object(FridaManager, 'get_running_servers')
    def test_is_server_running_false(self, mock_get):
        """Test is_server_running when no servers running"""
        mock_get.return_value = []
        
        fm = FridaManager()
        assert fm.is_server_running() is False
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_get_running_servers(self, mock_adb_class):
        """Test getting running servers"""
        mock_adb = MagicMock()
        mock_adb.shell.return_value = (
            "root      1234  1  0 10:00:00 ?     00:00:05 /data/local/tmp/frida-server-16.1.17-android-arm64",
            "",
            0
        )
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        servers = fm.get_running_servers()
        
        assert len(servers) == 1
        assert servers[0].pid == 1234
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_get_running_servers_empty(self, mock_adb_class):
        """Test getting running servers when none running"""
        mock_adb = MagicMock()
        mock_adb.shell.return_value = ("", "", 1)
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        servers = fm.get_running_servers()
        
        assert len(servers) == 0
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_check_port_listening_true(self, mock_adb_class):
        """Test port check when listening"""
        mock_adb = MagicMock()
        mock_adb.shell.return_value = ("tcp6  0  0 :::27042  :::*  LISTEN", "", 0)
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        assert fm.check_port_listening() is True
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_check_port_listening_false(self, mock_adb_class):
        """Test port check when not listening"""
        mock_adb = MagicMock()
        mock_adb.shell.return_value = ("", "", 1)
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        assert fm.check_port_listening() is False
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_is_server_installed_found(self, mock_adb_class):
        """Test checking if server is installed when it exists"""
        mock_adb = MagicMock()
        mock_adb.file_exists.return_value = True
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        path = fm.is_server_installed("16.1.17", "arm64")
        
        assert path == "/data/local/tmp/frida-server-16.1.17-android-arm64"
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_is_server_installed_not_found(self, mock_adb_class):
        """Test checking if server is installed when it doesn't exist"""
        mock_adb = MagicMock()
        mock_adb.file_exists.return_value = False
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        path = fm.is_server_installed("16.1.17", "arm64")
        
        assert path is None
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_list_installed_servers(self, mock_adb_class):
        """Test listing installed servers"""
        mock_adb = MagicMock()
        mock_adb.shell.return_value = (
            "/data/local/tmp/frida-server-16.1.17-android-arm64\n/data/local/tmp/frida-server-16.0.0-android-arm64",
            "",
            0
        )
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        servers = fm.list_installed_servers()
        
        assert len(servers) == 2
        assert "/data/local/tmp/frida-server-16.1.17-android-arm64" in servers
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_stop_server_success(self, mock_adb_class):
        """Test stopping server successfully"""
        mock_adb = MagicMock()
        mock_adb.shell_su.return_value = ("", "", 0)
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        result = fm.stop_server(1234)
        
        assert result is True
        mock_adb.shell_su.assert_called_with("kill -9 1234")
    
    @patch('f_for_frida.core.frida_manager.ADBClient')
    def test_get_server_status(self, mock_adb_class):
        """Test getting comprehensive server status"""
        mock_adb = MagicMock()
        # For get_running_servers
        mock_adb.shell.side_effect = [
            ("root 1234 /frida-server", "", 0),  # ps command
            ("tcp6 0 0 :::27042", "", 0),  # netstat command  
            ("/data/local/tmp/frida-server-16.1.17-android-arm64", "", 0),  # ls command
        ]
        mock_adb_class.return_value = mock_adb
        
        fm = FridaManager()
        status = fm.get_server_status()
        
        assert "running" in status
        assert "port_listening" in status
        assert "installed_servers" in status
