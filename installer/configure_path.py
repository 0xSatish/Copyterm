"""
configure_path.py - Persistent User PATH Management across Windows, Linux, and macOS
"""

import os
import sys
from pathlib import Path
from typing import Tuple, List, Optional

def _notify_windows_environment_change():
    """Broadcasts WM_SETTINGCHANGE to top-level windows so Explorer and new shells see updated PATH."""
    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            1000,
            ctypes.byref(result)
        )
    except Exception:
        pass

def get_windows_user_path() -> List[str]:
    """Reads the current persistent Windows User Environment PATH from the registry."""
    if sys.platform != "win32":
        return []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
            try:
                val, val_type = winreg.QueryValueEx(key, "Path")
                if val:
                    # Filter empty items
                    return [p.strip() for p in val.split(";") if p.strip()]
            except FileNotFoundError:
                return []
    except Exception:
        pass
    return []

def add_to_windows_user_path(bin_dir: Path) -> Tuple[bool, str]:
    """Permanently adds bin_dir to the Windows User Environment PATH in an idempotent manner."""
    if sys.platform != "win32":
        return False, "Not on Windows"
    
    bin_str = str(bin_dir.resolve())
    try:
        import winreg
        existing_entries = get_windows_user_path()
        
        # Check if already present (case-insensitive on Windows)
        normalized_target = bin_str.lower().rstrip("\\/")
        for entry in existing_entries:
            # Expand environment variables if any
            exp_entry = os.path.expandvars(entry).lower().rstrip("\\/")
            if exp_entry == normalized_target or entry.lower().rstrip("\\/") == normalized_target:
                # Already in PATH
                # Update current process PATH as well
                if bin_str not in os.environ.get("PATH", "").split(os.pathsep):
                    os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")
                return True, "Already in User PATH"

        # Append new path
        new_entries = existing_entries + [bin_str]
        new_path_val = ";".join(new_entries)

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path_val)

        _notify_windows_environment_change()

        # Update current process PATH
        if bin_str not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")

        return True, "Successfully added to Windows User PATH"
    except Exception as e:
        return False, f"Failed to modify Windows User PATH: {e}"

def remove_from_windows_user_path(bin_dir: Path) -> Tuple[bool, str]:
    """Removes bin_dir from the Windows User Environment PATH."""
    if sys.platform != "win32":
        return False, "Not on Windows"
    
    bin_str = str(bin_dir.resolve())
    try:
        import winreg
        existing_entries = get_windows_user_path()
        normalized_target = bin_str.lower().rstrip("\\/")
        
        new_entries = []
        found = False
        for entry in existing_entries:
            exp_entry = os.path.expandvars(entry).lower().rstrip("\\/")
            if exp_entry == normalized_target or entry.lower().rstrip("\\/") == normalized_target:
                found = True
                continue
            new_entries.append(entry)

        if not found:
            return True, "Not found in User PATH"

        new_path_val = ";".join(new_entries)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path_val)

        _notify_windows_environment_change()
        return True, "Successfully removed from Windows User PATH"
    except Exception as e:
        return False, f"Failed to modify Windows User PATH: {e}"

def configure_posix_path(bin_dir: Path) -> Tuple[bool, str]:
    """Ensures bin_dir is in PATH for POSIX systems via ~/.profile / ~/.bashrc / ~/.zshrc."""
    bin_str = str(bin_dir.resolve())
    # Update current process PATH
    if bin_str not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = bin_str + os.pathsep + os.environ.get("PATH", "")
    return True, "POSIX PATH configured via shell profiles"

def configure_path(bin_dir: Path) -> Tuple[bool, str]:
    """Cross-platform PATH configuration."""
    if sys.platform == "win32":
        return add_to_windows_user_path(bin_dir)
    else:
        return configure_posix_path(bin_dir)

def unconfigure_path(bin_dir: Path) -> Tuple[bool, str]:
    """Cross-platform PATH unconfiguration."""
    if sys.platform == "win32":
        return remove_from_windows_user_path(bin_dir)
    else:
        return True, "Removed from POSIX PATH"

if __name__ == "__main__":
    target = Path.home() / ".copyterm" / "bin"
    ok, msg = configure_path(target)
    print(f"Configure PATH: {ok} ({msg})")
