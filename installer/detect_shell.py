"""
detect_shell.py - Active and Installed Shell Detection
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

def detect_current_shell() -> str:
    """Detect the active shell running the installer or parent process."""
    if os.environ.get("PSExecutionPolicyPreference") or os.environ.get("PSModulePath"):
        # Check if PowerShell 7 (pwsh) or Windows PowerShell (powershell)
        if "pwsh" in sys.executable.lower() or os.environ.get("POWERSHELL_DISTRIBUTION_CHANNEL"):
            return "PowerShell Core"
        return "PowerShell"
    
    shell_env = os.environ.get("SHELL", "")
    if shell_env:
        shell_base = Path(shell_env).name.lower()
        if "zsh" in shell_base:
            return "zsh"
        elif "bash" in shell_base:
            return "bash"
        elif "fish" in shell_base:
            return "fish"
        return shell_base

    if sys.platform == "win32":
        # Check parent process or prompt environment
        if os.environ.get("PROMPT"):
            return "cmd"
        return "PowerShell"

    return "bash"

def detect_installed_shells() -> List[str]:
    """Detect all available/installed shells on the system."""
    installed = []
    
    if sys.platform == "win32":
        if shutil.which("powershell.exe") or Path(os.environ.get("SystemRoot", "C:\\Windows")).joinpath("System32\\WindowsPowerShell\\v1.0\\powershell.exe").exists():
            installed.append("PowerShell")
        if shutil.which("pwsh.exe") or shutil.which("pwsh"):
            installed.append("PowerShell Core (pwsh)")
        if shutil.which("cmd.exe"):
            installed.append("cmd")
        if shutil.which("bash.exe") or shutil.which("bash"):
            installed.append("Git Bash / Bash")
        if shutil.which("zsh.exe") or shutil.which("zsh"):
            installed.append("zsh")
    else:
        for sh in ["bash", "zsh", "fish", "sh", "pwsh"]:
            if shutil.which(sh):
                installed.append(sh)
                
    return installed

if __name__ == "__main__":
    print(f"Current Shell: {detect_current_shell()}")
    print(f"Installed Shells: {', '.join(detect_installed_shells())}")
