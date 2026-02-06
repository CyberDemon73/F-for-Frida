"""
Download utilities for Frida server binaries
"""

import os
import subprocess
import requests
from typing import Optional
from shutil import which
from pathlib import Path

from tqdm import tqdm

from .logger import get_logger

logger = get_logger(__name__)

# GitHub API and release URLs
FRIDA_RELEASES_API = "https://api.github.com/repos/frida/frida/releases/latest"
FRIDA_RELEASE_URL = "https://github.com/frida/frida/releases/download/{version}/frida-server-{version}-android-{arch}.xz"


def check_xz_installed() -> bool:
    """
    Check if 'xz' command is available on the system.
    
    Returns:
        True if xz is installed
    """
    return which("xz") is not None


def get_latest_frida_version() -> Optional[str]:
    """
    Get the latest Frida version from GitHub releases.
    
    Returns:
        Version string or None on failure
    """
    try:
        response = requests.get(FRIDA_RELEASES_API, timeout=10)
        response.raise_for_status()
        data = response.json()
        version = data.get("tag_name", "").lstrip("v")
        logger.info(f"Latest Frida version: {version}")
        return version
    except requests.RequestException as e:
        logger.error(f"Failed to fetch latest Frida version: {e}")
        return None


def get_available_versions(limit: int = 10) -> list:
    """
    Get list of available Frida versions.
    
    Args:
        limit: Maximum number of versions to return
        
    Returns:
        List of version strings
    """
    try:
        response = requests.get(
            "https://api.github.com/repos/frida/frida/releases",
            params={"per_page": limit},
            timeout=10
        )
        response.raise_for_status()
        releases = response.json()
        return [r["tag_name"].lstrip("v") for r in releases if not r.get("prerelease")]
    except requests.RequestException as e:
        logger.error(f"Failed to fetch Frida versions: {e}")
        return []


def download_file(url: str, destination: str, show_progress: bool = True) -> bool:
    """
    Download a file from URL with progress bar.
    
    Args:
        url: Download URL
        destination: Local file path
        show_progress: Show download progress
        
    Returns:
        True if successful
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        if show_progress:
            progress = tqdm(
                total=total_size,
                unit='iB',
                unit_scale=True,
                desc=os.path.basename(destination)
            )
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(block_size):
                if show_progress:
                    progress.update(len(chunk))
                f.write(chunk)
        
        if show_progress:
            progress.close()
        
        return True
        
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False


def extract_xz(xz_path: str, keep_original: bool = False) -> Optional[str]:
    """
    Extract an XZ compressed file.
    
    Args:
        xz_path: Path to .xz file
        keep_original: Keep the compressed file after extraction
        
    Returns:
        Path to extracted file or None on failure
    """
    if not check_xz_installed():
        logger.error("'xz' command not found. Please install xz-utils.")
        return None
    
    try:
        args = ["xz", "--decompress"]
        if keep_original:
            args.append("--keep")
        else:
            args.append("--force")
        args.append(xz_path)
        
        result = subprocess.run(args, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"XZ extraction failed: {result.stderr}")
            return None
        
        # Return path without .xz extension
        return xz_path.rstrip(".xz")
        
    except subprocess.SubprocessError as e:
        logger.error(f"XZ extraction error: {e}")
        return None


def download_frida_server(
    version: str,
    architecture: str,
    download_dir: Optional[str] = None,
    show_progress: bool = True
) -> Optional[str]:
    """
    Download and extract Frida server binary.
    
    Args:
        version: Frida version (e.g., "16.1.17")
        architecture: Target architecture (arm64, arm, x86, x86_64)
        download_dir: Directory to save files (default: current directory)
        show_progress: Show download progress
        
    Returns:
        Path to extracted binary or None on failure
    """
    if not check_xz_installed():
        logger.error("'xz' command not found. Please install xz-utils.")
        logger.error("  - Windows: Install from https://tukaani.org/xz/ or use 'winget install xz'")
        logger.error("  - Linux: sudo apt install xz-utils")
        logger.error("  - macOS: brew install xz")
        return None
    
    download_dir = download_dir or os.getcwd()
    os.makedirs(download_dir, exist_ok=True)
    
    # Build download URL
    url = FRIDA_RELEASE_URL.format(version=version, arch=architecture)
    filename = f"frida-server-{version}-android-{architecture}.xz"
    xz_path = os.path.join(download_dir, filename)
    
    logger.info(f"Downloading Frida server {version} for {architecture}")
    
    # Download
    if not download_file(url, xz_path, show_progress):
        return None
    
    # Extract
    logger.info("Extracting Frida server...")
    extracted_path = extract_xz(xz_path)
    
    if extracted_path:
        logger.info(f"Frida server ready: {extracted_path}")
    
    return extracted_path
