"""
Logging utilities for F-for-Frida
"""

import logging
import sys
from typing import Optional
from pathlib import Path

# Default log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_SIMPLE = "%(levelname)s - %(message)s"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
    verbose: bool = False
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional file path for logging
        console: Enable console logging
        verbose: Use verbose format with timestamps
        
    Returns:
        Root logger
    """
    root_logger = logging.getLogger("f_for_frida")
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT if verbose else LOG_FORMAT_SIMPLE)
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    if name.startswith("f_for_frida"):
        return logging.getLogger(name)
    return logging.getLogger(f"f_for_frida.{name}")
