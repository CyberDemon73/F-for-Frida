"""
Tests for Configuration module
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch
from f_for_frida.utils.config import Config, ConfigManager, get_config


class TestConfig:
    """Tests for Config dataclass"""
    
    def test_default_values(self):
        """Test default configuration values"""
        config = Config()
        
        assert config.default_device is None
        assert config.default_version is None
        assert config.frida_port == 27042
        assert config.wireless_port == 5555
        assert config.auto_start is False
        assert config.verbose is False
    
    def test_custom_values(self):
        """Test custom configuration values"""
        config = Config(
            default_device="ABC123",
            default_version="16.1.17",
            auto_start=True
        )
        
        assert config.default_device == "ABC123"
        assert config.default_version == "16.1.17"
        assert config.auto_start is True
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        config = Config(default_device="ABC123")
        d = config.to_dict()
        
        assert isinstance(d, dict)
        assert d["default_device"] == "ABC123"
        assert "frida_port" in d
        assert "wireless_port" in d
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "default_device": "ABC123",
            "default_version": "16.1.17",
            "frida_port": 27042
        }
        
        config = Config.from_dict(data)
        
        assert config.default_device == "ABC123"
        assert config.default_version == "16.1.17"
        assert config.frida_port == 27042
    
    def test_from_dict_with_unknown_fields(self):
        """Test creation from dictionary with unknown fields"""
        data = {
            "default_device": "ABC123",
            "unknown_field": "value",
            "another_unknown": 123
        }
        
        # Should not raise, just ignore unknown fields
        config = Config.from_dict(data)
        
        assert config.default_device == "ABC123"
        assert not hasattr(config, "unknown_field")


class TestConfigManager:
    """Tests for ConfigManager class"""
    
    def test_init_no_path(self):
        """Test initialization without path"""
        cm = ConfigManager()
        assert cm.config_path is None
    
    def test_init_with_path(self, tmp_path):
        """Test initialization with path"""
        config_file = tmp_path / "config.json"
        cm = ConfigManager(str(config_file))
        assert cm.config_path == config_file
    
    def test_load_default_config(self):
        """Test loading default config when no file exists"""
        cm = ConfigManager()
        config = cm.load()
        
        assert isinstance(config, Config)
        assert config.frida_port == 27042
    
    def test_load_json_config(self, tmp_path):
        """Test loading JSON config file"""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "default_device": "ABC123",
            "frida_port": 27042
        }))
        
        cm = ConfigManager(str(config_file))
        config = cm.load()
        
        assert config.default_device == "ABC123"
    
    def test_save_config(self, tmp_path):
        """Test saving configuration"""
        config_file = tmp_path / "config.json"
        cm = ConfigManager(str(config_file))
        
        config = Config(default_device="ABC123")
        result = cm.save(config)
        
        assert result is True
        assert config_file.exists()
        
        # Verify contents
        data = json.loads(config_file.read_text())
        assert data["default_device"] == "ABC123"
    
    def test_get_config_value(self, tmp_path):
        """Test getting a config value"""
        config_file = tmp_path / "config.json"
        cm = ConfigManager(str(config_file))
        
        # Load default config
        cm.load()
        
        value = cm.get("frida_port")
        assert value == 27042
    
    def test_get_config_value_default(self, tmp_path):
        """Test getting a config value with default"""
        config_file = tmp_path / "config.json"
        cm = ConfigManager(str(config_file))
        cm.load()
        
        value = cm.get("nonexistent", "default")
        assert value == "default"
    
    def test_set_config_value(self, tmp_path):
        """Test setting a config value"""
        config_file = tmp_path / "config.json"
        cm = ConfigManager(str(config_file))
        cm.load()
        
        result = cm.set("default_device", "NEW123")
        
        assert result is True
        assert cm.get("default_device") == "NEW123"
    
    def test_set_unknown_config_value(self, tmp_path):
        """Test setting unknown config value"""
        config_file = tmp_path / "config.json"
        cm = ConfigManager(str(config_file))
        cm.load()
        
        result = cm.set("unknown_key", "value")
        
        assert result is False
    
    def test_env_override(self, tmp_path):
        """Test environment variable override"""
        config_file = tmp_path / "config.json"
        
        with patch.dict('os.environ', {'F4F_DEFAULT_DEVICE': 'ENV_DEVICE'}):
            cm = ConfigManager(str(config_file))
            config = cm.load()
            
            assert config.default_device == "ENV_DEVICE"
    
    def test_env_override_port(self, tmp_path):
        """Test environment variable override for port"""
        config_file = tmp_path / "config.json"
        
        with patch.dict('os.environ', {'F4F_FRIDA_PORT': '12345'}):
            cm = ConfigManager(str(config_file))
            config = cm.load()
            
            assert config.frida_port == 12345
    
    def test_env_override_boolean(self, tmp_path):
        """Test environment variable override for boolean"""
        config_file = tmp_path / "config.json"
        
        with patch.dict('os.environ', {'F4F_VERBOSE': 'true'}):
            cm = ConfigManager(str(config_file))
            config = cm.load()
            
            assert config.verbose is True
