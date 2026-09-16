"""
install_macos.py - macOS Platform Installer Implementation
"""

from pathlib import Path
from typing import Dict, Any
from .install_linux import install_linux, uninstall_linux

def install_macos(repo_root: Path) -> Dict[str, Any]:
    return install_linux(repo_root)

def uninstall_macos() -> Dict[str, Any]:
    return uninstall_linux()
