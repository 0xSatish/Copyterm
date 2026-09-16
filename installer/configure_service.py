"""
configure_service.py - User-level Service Lifecycle Management
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

def is_systemd_user_available() -> bool:
    if sys.platform != "linux" or not shutil.which("systemctl"):
        return False
    try:
        res = subprocess.run(["systemctl", "--user", "is-system-running"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        return res.returncode in (0, 1)
    except Exception:
        return False

def configure_systemd_user_service(bin_dir: Path) -> Tuple[bool, str]:
    """Creates and enables a lightweight user-level systemd service if systemd is active."""
    if not is_systemd_user_available():
        return True, "N/A (systemd user daemon not required for core CLI)"
    
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_file = service_dir / "copyterm.service"
    
    cpt_bin = bin_dir / "cpt"
    if not cpt_bin.exists():
        cpt_bin = bin_dir / "copyterm.py"

    service_content = f"""[Unit]
Description=CopyTerm Terminal Capture Bridge Service
Documentation=https://github.com/copyterm/copyterm
After=default.target

[Service]
Type=simple
ExecStart={sys.executable} {bin_dir}/copyterm.py clean-sessions
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=default.target
"""
    try:
        service_dir.mkdir(parents=True, exist_ok=True)
        service_file.write_text(service_content, encoding="utf-8")
        subprocess.run(["systemctl", "--user", "daemon-reload"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        subprocess.run(["systemctl", "--user", "enable", "copyterm.service"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True, "Enabled copyterm.service"
    except Exception as e:
        return False, f"Failed to configure systemd service: {e}"

def unconfigure_systemd_user_service() -> Tuple[bool, str]:
    if not is_systemd_user_available():
        return True, "N/A"
    service_file = Path.home() / ".config" / "systemd" / "user" / "copyterm.service"
    try:
        subprocess.run(["systemctl", "--user", "stop", "copyterm.service"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        subprocess.run(["systemctl", "--user", "disable", "copyterm.service"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if service_file.exists():
            service_file.unlink()
        subprocess.run(["systemctl", "--user", "daemon-reload"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True, "Disabled and removed copyterm.service"
    except Exception as e:
        return False, f"Failed to remove systemd service: {e}"

def configure_service(bin_dir: Path) -> Tuple[bool, str]:
    if sys.platform == "win32":
        return True, "N/A (Windows background service not required; IDE bridge runs in-process)"
    elif sys.platform == "linux" and is_systemd_user_available():
        return configure_systemd_user_service(bin_dir)
    return True, "N/A"

def unconfigure_service() -> Tuple[bool, str]:
    if sys.platform == "win32":
        return True, "N/A"
    elif sys.platform == "linux":
        return unconfigure_systemd_user_service()
    return True, "N/A"
