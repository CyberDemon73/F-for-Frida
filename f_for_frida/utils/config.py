"""
Configuration management for F-for-Frida
Supports YAML/JSON config files and environment variables
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from .logger import get_logger

logger = get_logger(__name__)

# Default config locations
DEFAULT_CONFIG_PATHS = [
    Path.home() / ".f4f" / "config.yaml",
    Path.home() / ".f4f" / "config.json",
    Path.home() / ".config" / "f4f" / "config.yaml",
    Path(".f4f.yaml"),
    Path(".f4f.json"),
]


@dataclass
class Config:
    """F-for-Frida configuration"""
    
    # Device settings
    default_device: Optional[str] = None
    preferred_devices: list = field(default_factory=list)
    
    # Frida settings
    default_version: Optional[str] = None
    auto_start: bool = False
    frida_port: int = 27042
    
    # Server settings
    server_path: str = "/data/local/tmp"
    auto_cleanup: bool = True
    keep_binaries: int = 3  # Keep last N versions
    
    # Download settings
    download_dir: Optional[str] = None
    show_progress: bool = True
    
    # Wireless ADB
    wireless_port: int = 5555
    auto_connect_wireless: bool = False
    saved_wireless_devices: list = field(default_factory=list)
    
    # Scripts
    scripts_dir: Optional[str] = None
    
    # Logging
    log_file: Optional[str] = None
    verbose: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        # Filter only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


class ConfigManager:
    """Manages configuration loading and saving"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self._config: Optional[Config] = None
    
    def _find_config_file(self) -> Optional[Path]:
        """Find existing config file."""
        if self.config_path and self.config_path.exists():
            return self.config_path
        
        for path in DEFAULT_CONFIG_PATHS:
            if path.exists():
                logger.debug(f"Found config file: {path}")
                return path
        
        return None
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML config file."""
        try:
            import yaml
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            logger.warning("PyYAML not installed, falling back to JSON parsing")
            # Try parsing as JSON (subset of YAML)
            return self._load_json(path)
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON config file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def load(self) -> Config:
        """Load configuration from file or return defaults."""
        if self._config:
            return self._config
        
        config_file = self._find_config_file()
        
        if config_file:
            try:
                if config_file.suffix in ['.yaml', '.yml']:
                    data = self._load_yaml(config_file)
                else:
                    data = self._load_json(config_file)
                
                self._config = Config.from_dict(data)
                logger.info(f"Loaded config from {config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                self._config = Config()
        else:
            self._config = Config()
        
        # Override with environment variables
        self._apply_env_overrides()
        
        return self._config
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        env_mappings = {
            'F4F_DEFAULT_DEVICE': ('default_device', str),
            'F4F_DEFAULT_VERSION': ('default_version', str),
            'F4F_FRIDA_PORT': ('frida_port', int),
            'F4F_WIRELESS_PORT': ('wireless_port', int),
            'F4F_VERBOSE': ('verbose', lambda x: x.lower() in ('true', '1', 'yes')),
            'F4F_SCRIPTS_DIR': ('scripts_dir', str),
            'F4F_DOWNLOAD_DIR': ('download_dir', str),
        }
        
        for env_var, (field, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                try:
                    setattr(self._config, field, converter(value))
                    logger.debug(f"Override from env: {field}={value}")
                except (ValueError, TypeError):
                    pass
    
    def save(self, config: Optional[Config] = None, path: Optional[str] = None):
        """Save configuration to file."""
        config = config or self._config or Config()
        save_path = Path(path) if path else self.config_path
        
        if not save_path:
            save_path = DEFAULT_CONFIG_PATHS[0]
        
        # Create directory if needed
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = config.to_dict()
        
        try:
            if save_path.suffix in ['.yaml', '.yml']:
                import yaml
                with open(save_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:
                with open(save_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            logger.info(f"Config saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        config = self.load()
        return getattr(config, key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a config value and save."""
        config = self.load()
        if hasattr(config, key):
            setattr(config, key, value)
            return self.save(config)
        return False


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> Config:
    """Get the global configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.load()


def get_config_manager() -> ConfigManager:
    """Get the global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
