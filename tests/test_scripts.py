"""
Tests for Scripts module
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from f_for_frida.core.scripts import ScriptManager, FridaScript, BUILTIN_SCRIPTS


class TestFridaScript:
    """Tests for FridaScript dataclass"""
    
    def test_creation(self):
        """Test FridaScript creation"""
        script = FridaScript(
            name="test-script",
            description="A test script",
            content="console.log('test');",
            category="test"
        )
        
        assert script.name == "test-script"
        assert script.description == "A test script"
        assert script.category == "test"
        assert script.android_only is True
    
    def test_save(self, tmp_path):
        """Test saving script to file"""
        script = FridaScript(
            name="test-script",
            description="Test",
            content="console.log('test');"
        )
        
        path = tmp_path / "test.js"
        result = script.save(str(path))
        
        assert result is True
        assert path.exists()
        assert path.read_text() == "console.log('test');"


class TestBuiltinScripts:
    """Tests for built-in scripts"""
    
    def test_ssl_bypass_exists(self):
        """Test SSL bypass script exists"""
        assert "ssl-pinning-bypass" in BUILTIN_SCRIPTS
        script = BUILTIN_SCRIPTS["ssl-pinning-bypass"]
        assert script.category == "network"
        assert "Java.perform" in script.content
    
    def test_root_bypass_exists(self):
        """Test root bypass script exists"""
        assert "root-detection-bypass" in BUILTIN_SCRIPTS
        script = BUILTIN_SCRIPTS["root-detection-bypass"]
        assert script.category == "security"
    
    def test_anti_debug_exists(self):
        """Test anti-debug script exists"""
        assert "anti-debug-bypass" in BUILTIN_SCRIPTS
        script = BUILTIN_SCRIPTS["anti-debug-bypass"]
        assert script.category == "security"
    
    def test_method_tracer_exists(self):
        """Test method tracer script exists"""
        assert "method-tracer" in BUILTIN_SCRIPTS
        script = BUILTIN_SCRIPTS["method-tracer"]
        assert script.category == "analysis"
    
    def test_crypto_logger_exists(self):
        """Test crypto logger script exists"""
        assert "crypto-logger" in BUILTIN_SCRIPTS
        script = BUILTIN_SCRIPTS["crypto-logger"]
        assert script.category == "crypto"
    
    def test_http_logger_exists(self):
        """Test HTTP logger script exists"""
        assert "http-logger" in BUILTIN_SCRIPTS
        script = BUILTIN_SCRIPTS["http-logger"]
        assert script.category == "network"
    
    def test_all_scripts_have_content(self):
        """Test all scripts have content"""
        for name, script in BUILTIN_SCRIPTS.items():
            assert script.content, f"Script {name} has no content"
            assert len(script.content) > 50, f"Script {name} content too short"


class TestScriptManager:
    """Tests for ScriptManager class"""
    
    def test_init(self, tmp_path):
        """Test ScriptManager initialization"""
        with patch('f_for_frida.core.scripts.get_config') as mock_config:
            mock_config.return_value.scripts_dir = str(tmp_path)
            sm = ScriptManager(scripts_dir=str(tmp_path))
            assert sm.scripts_dir == tmp_path
    
    def test_list_builtin(self, tmp_path):
        """Test listing built-in scripts"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        scripts = sm.list_builtin()
        
        assert len(scripts) == len(BUILTIN_SCRIPTS)
    
    def test_get_builtin(self, tmp_path):
        """Test getting a built-in script"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        script = sm.get_builtin("ssl-pinning-bypass")
        
        assert script is not None
        assert script.name == "ssl-pinning-bypass"
    
    def test_get_builtin_not_found(self, tmp_path):
        """Test getting non-existent built-in script"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        script = sm.get_builtin("nonexistent")
        
        assert script is None
    
    def test_save_and_get_custom(self, tmp_path):
        """Test saving and retrieving custom script"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        
        content = "console.log('custom script');"
        path = sm.save_script("my-script", content)
        
        assert path.exists()
        
        retrieved = sm.get_custom("my-script")
        assert retrieved == content
    
    def test_export_builtin(self, tmp_path):
        """Test exporting built-in script"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        
        path = sm.export_builtin("ssl-pinning-bypass")
        
        assert path is not None
        assert path.exists()
        assert "Java.perform" in path.read_text()
    
    def test_export_builtin_not_found(self, tmp_path):
        """Test exporting non-existent script"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        
        path = sm.export_builtin("nonexistent")
        
        assert path is None
    
    def test_get_by_category(self, tmp_path):
        """Test getting scripts by category"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        
        network_scripts = sm.get_by_category("network")
        
        assert len(network_scripts) >= 1
        assert all(s.category == "network" for s in network_scripts)
    
    def test_get_categories(self, tmp_path):
        """Test getting all categories"""
        sm = ScriptManager(scripts_dir=str(tmp_path))
        
        categories = sm.get_categories()
        
        assert "network" in categories
        assert "security" in categories
        assert "crypto" in categories
