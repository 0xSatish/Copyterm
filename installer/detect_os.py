"""
detect_os.py - Environment, OS, Architecture, Terminal, and IDE Detection
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

def detect_os() -> str:
    """Returns 'windows', 'linux', 'macos', or generic platform name."""
    p = sys.platform.lower()
    if p in ("win32", "cygwin", "msys"):
        return "windows"
    elif p.startswith("linux"):
        return "linux"
    elif p in ("darwin", "macos"):
        return "macos"
    return p

def detect_distro() -> Optional[str]:
    """Detect Linux distribution name (e.g. 'ubuntu', 'debian', 'fedora', 'arch')."""
    if detect_os() != "linux":
        return None
    try:
        os_release = Path("/etc/os-release")
        if os_release.exists():
            for line in os_release.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("ID="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'").lower()
                elif line.startswith("PRETTY_NAME=") and not line.startswith("ID="):
                    pretty = line.split("=", 1)[1].strip().strip('"').strip("'").lower()
                    for d in ["ubuntu", "debian", "fedora", "arch", "centos", "rhel", "alpine", "opensuse", "manjaro"]:
                        if d in pretty:
                            return d
    except Exception:
        pass
    return "linux"

def detect_arch() -> str:
    """Returns normalized architecture name: 'x64', 'arm64', 'x86', 'arm'."""
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64", "x64"):
        return "x64"
    elif machine in ("arm64", "aarch64"):
        return "arm64"
    elif machine in ("i386", "i686", "x86"):
        return "x86"
    return machine

def detect_terminal() -> str:
    """Detects active terminal emulator."""
    if os.environ.get("WT_SESSION"):
        return "Windows Terminal"
    if os.environ.get("TERM_PROGRAM"):
        term_prog = os.environ.get("TERM_PROGRAM")
        if "vscode" in term_prog.lower() or "antigravity" in term_prog.lower():
            if os.environ.get("ANTIGRAVITY_PID") or "antigravity" in term_prog.lower() or Path.home().joinpath(".antigravity-ide").exists():
                return "Antigravity / VS Code Terminal"
            return "VS Code Terminal"
        return term_prog
    if os.environ.get("TMUX"):
        return "tmux"
    if os.environ.get("SSH_TTY") or os.environ.get("SSH_CLIENT"):
        return "SSH Terminal"
    if detect_os() == "windows":
        return "Windows Console (conhost)"
    return os.environ.get("TERM", "xterm-256color")

def detect_ide() -> Optional[str]:
    """Detects supported IDE environment if available."""
    ag_ext = Path.home() / ".antigravity-ide" / "extensions"
    vs_ext = Path.home() / ".vscode" / "extensions"
    ides = []
    if ag_ext.parent.exists():
        ides.append("Antigravity")
    if vs_ext.parent.exists():
        ides.append("VS Code")
    if ides:
        return ", ".join(ides)
    return None

def is_systemd_available() -> bool:
    """Checks if systemd user-level service manager is available."""
    if detect_os() != "linux":
        return False
    if not shutil.which("systemctl"):
        return False
    try:
        res = subprocess.run(["systemctl", "--user", "is-system-running"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
        return res.returncode in (0, 1) # 0=running, 1=degraded/running
    except Exception:
        return False

def get_system_summary() -> Dict[str, Any]:
    os_name = detect_os()
    distro = detect_distro()
    arch = detect_arch()
    term = detect_terminal()
    ide = detect_ide()
    systemd = is_systemd_available()
    
    os_display = "Windows"
    if os_name == "windows":
        os_display = f"Windows ({platform.release()})"
    elif os_name == "linux":
        os_display = f"Linux ({distro.capitalize() if distro else 'Generic'})"
    elif os_name == "macos":
        os_display = f"macOS ({platform.mac_ver()[0]})"

    return {
        "os": os_name,
        "os_display": os_display,
        "distro": distro,
        "arch": arch,
        "terminal": term,
        "ide": ide or "Not detected",
        "systemd": "Available" if systemd else "N/A"
    }

if __name__ == "__main__":
    import json
    print(json.dumps(get_system_summary(), indent=2))
