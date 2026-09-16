"""
configure_shell.py - Idempotent Shell Profile Management (PowerShell, Bash, Zsh)
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

MARKER_START = "# >>> CopyTerm managed block >>>"
MARKER_END   = "# <<< CopyTerm managed block <<<"

def get_powershell_snippet(data_dir: Path) -> str:
    return f"""{MARKER_START}
$__copyterm_ps1 = [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm", "integrations", "powershell", "copyterm.ps1")
if (Test-Path $__copyterm_ps1) {{ . $__copyterm_ps1 }}
{MARKER_END}"""

def get_bash_snippet(data_dir: Path) -> str:
    return f"""{MARKER_START}
export PATH="$HOME/.copyterm/bin:$PATH"
__copyterm_bash="${{COPYTERM_DATA_DIR:-$HOME/.copyterm}}/integrations/bash/copyterm.bash"
[ -f "$__copyterm_bash" ] && . "$__copyterm_bash"
{MARKER_END}"""

def get_zsh_snippet(data_dir: Path) -> str:
    return f"""{MARKER_START}
export PATH="$HOME/.copyterm/bin:$PATH"
__copyterm_zsh="${{COPYTERM_DATA_DIR:-$HOME/.copyterm}}/integrations/zsh/copyterm.zsh"
[ -f "$__copyterm_zsh" ] && . "$__copyterm_zsh"
{MARKER_END}"""

def discover_powershell_profiles() -> List[Path]:
    """Finds all candidate PowerShell profile paths."""
    candidates = []
    home = Path.home()
    userprofile = Path(os.environ.get("USERPROFILE", str(home)))

    # Windows PowerShell 5.1 & PowerShell 7+ standard document paths
    base_docs = [
        home / "Documents",
        userprofile / "Documents",
        home / "OneDrive" / "Documents",
        userprofile / "OneDrive" / "Documents",
    ]

    for doc in base_docs:
        # Windows PowerShell (5.1)
        candidates.append(doc / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1")
        candidates.append(doc / "WindowsPowerShell" / "profile.ps1")
        # PowerShell Core (7+)
        candidates.append(doc / "PowerShell" / "Microsoft.PowerShell_profile.ps1")
        candidates.append(doc / "PowerShell" / "profile.ps1")

    # POSIX pwsh path
    candidates.append(home / ".config" / "powershell" / "Microsoft.PowerShell_profile.ps1")

    # Remove duplicates preserving order
    seen = set()
    result = []
    for c in candidates:
        norm = str(c.resolve() if c.exists() else c).lower() if sys.platform == "win32" else str(c)
        if norm not in seen:
            seen.add(norm)
            result.append(c)

    return result

def discover_bash_profiles() -> List[Path]:
    """Finds candidate Bash profile paths."""
    home = Path.home()
    return [
        home / ".bashrc",
        home / ".bash_profile",
        home / ".profile"
    ]

def discover_zsh_profiles() -> List[Path]:
    """Finds candidate Zsh profile paths."""
    home = Path.home()
    return [
        home / ".zshrc",
        home / ".zprofile"
    ]

def apply_managed_block(file_path: Path, snippet: str) -> Tuple[bool, str]:
    """Idempotently writes or updates a managed block in a profile file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = ""
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8", errors="replace")

        # Pattern matching existing block (including legacy blocks)
        pattern = re.compile(
            r'(?:#|::)\s*>>>\s*CopyTerm.*?(?:#|::)\s*<<<\s*CopyTerm.*?<<<(?:\r?\n)?',
            re.DOTALL | re.IGNORECASE
        )

        if pattern.search(content):
            # Replace existing block
            new_content = pattern.sub(snippet + "\n", content)
            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")
                return True, f"Updated managed block in {file_path.name}"
            return True, f"Managed block already up to date in {file_path.name}"
        else:
            # Append block cleanly
            if content and not content.endswith("\n"):
                content += "\n"
            content += "\n" + snippet + "\n"
            file_path.write_text(content, encoding="utf-8")
            return True, f"Added managed block to {file_path.name}"
    except Exception as e:
        return False, f"Failed to modify {file_path}: {e}"

def remove_managed_block(file_path: Path) -> Tuple[bool, str]:
    """Removes the managed block from a profile file."""
    try:
        if not file_path.exists():
            return True, "File does not exist"
        content = file_path.read_text(encoding="utf-8", errors="replace")
        pattern = re.compile(
            r'\n*(?:#|::)\s*>>>\s*CopyTerm.*?(?:#|::)\s*<<<\s*CopyTerm.*?<<<\n*',
            re.DOTALL | re.IGNORECASE
        )
        if pattern.search(content):
            new_content = pattern.sub("\n", content).strip() + "\n"
            file_path.write_text(new_content, encoding="utf-8")
            return True, f"Removed managed block from {file_path.name}"
        return True, "No managed block found"
    except Exception as e:
        return False, f"Failed to remove from {file_path}: {e}"

def get_cmd_autorun_snippet(data_dir: Path) -> str:
    init_cmd = data_dir / "integrations" / "cmd" / "copyterm_init.cmd"
    return f'if exist "{init_cmd}" call "{init_cmd}"'

def install_cmd_autorun(data_dir: Path) -> Tuple[bool, str]:
    """Configures CMD AutoRun in Windows Registry."""
    if sys.platform != "win32":
        return True, "CMD AutoRun not applicable on non-Windows"
    try:
        import winreg
        key_path = r"Software\Microsoft\Command Processor"
        snippet = get_cmd_autorun_snippet(data_dir)

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current_val, val_type = winreg.QueryValueEx(key, "AutoRun")
            except FileNotFoundError:
                current_val = ""
                val_type = winreg.REG_SZ

            if "copyterm_init.cmd" in current_val:
                return True, "CMD AutoRun already configured"

            if current_val.strip():
                new_val = f"{current_val.rstrip()} & {snippet}"
            else:
                new_val = snippet

            winreg.SetValueEx(key, "AutoRun", 0, winreg.REG_SZ, new_val)
            return True, "Configured CMD AutoRun in registry"
    except Exception as e:
        return False, f"Failed to configure CMD AutoRun: {e}"

def uninstall_cmd_autorun() -> Tuple[bool, str]:
    """Removes CMD AutoRun configuration from Windows Registry."""
    if sys.platform != "win32":
        return True, "CMD AutoRun not applicable on non-Windows"
    try:
        import winreg
        key_path = r"Software\Microsoft\Command Processor"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            try:
                current_val, val_type = winreg.QueryValueEx(key, "AutoRun")
            except FileNotFoundError:
                return True, "CMD AutoRun not set"

            if "copyterm_init.cmd" not in current_val:
                return True, "CMD AutoRun has no CopyTerm hooks"

            # Remove snippet cleanly
            parts = [p.strip() for p in current_val.split("&") if "copyterm_init.cmd" not in p and p.strip()]
            new_val = " & ".join(parts)
            if new_val:
                winreg.SetValueEx(key, "AutoRun", 0, winreg.REG_SZ, new_val)
            else:
                try:
                    winreg.DeleteValue(key, "AutoRun")
                except Exception:
                    winreg.SetValueEx(key, "AutoRun", 0, winreg.REG_SZ, "")
            return True, "Removed CopyTerm from CMD AutoRun"
    except Exception as e:
        return False, f"Failed to remove CMD AutoRun: {e}"

def install_all_shell_hooks(data_dir: Path) -> List[Dict[str, Any]]:
    """Installs managed hooks into all relevant shell profiles on the machine."""
    results = []

    # PowerShell
    ps_snippet = get_powershell_snippet(data_dir)
    for p in discover_powershell_profiles():
        # Only install into directories that exist or standard ones
        if p.parent.exists() or "Documents" in str(p):
            ok, msg = apply_managed_block(p, ps_snippet)
            results.append({"shell": "PowerShell", "path": str(p), "ok": ok, "message": msg})

    # CMD (Windows)
    # CMD AutoRun is intentionally disabled by default to prevent recursive cmd.exe process spawning.
    # CMD users use cpt / copyterm directly via PATH (%USERPROFILE%\.copyterm\bin).
    if sys.platform == "win32":
        results.append({
            "shell": "CMD",
            "path": "HKCU\\Software\\Microsoft\\Command Processor\\AutoRun",
            "ok": True,
            "message": "CMD direct PATH integration active (AutoRun disabled for safety)"
        })

    # Bash
    if sys.platform != "win32" or (Path.home() / ".bashrc").exists():
        bash_snippet = get_bash_snippet(data_dir)
        for p in discover_bash_profiles():
            if p.exists() or p.name == ".bashrc":
                ok, msg = apply_managed_block(p, bash_snippet)
                results.append({"shell": "Bash", "path": str(p), "ok": ok, "message": msg})

    # Zsh
    if sys.platform != "win32" or (Path.home() / ".zshrc").exists():
        zsh_snippet = get_zsh_snippet(data_dir)
        for p in discover_zsh_profiles():
            if p.exists() or p.name == ".zshrc":
                ok, msg = apply_managed_block(p, zsh_snippet)
                results.append({"shell": "Zsh", "path": str(p), "ok": ok, "message": msg})

    return results

def uninstall_all_shell_hooks() -> List[Dict[str, Any]]:
    """Removes managed hooks from all discovered profiles."""
    results = []
    all_profiles = discover_powershell_profiles() + discover_bash_profiles() + discover_zsh_profiles()
    for p in all_profiles:
        if p.exists():
            ok, msg = remove_managed_block(p)
            results.append({"path": str(p), "ok": ok, "message": msg})

    if sys.platform == "win32":
        ok_cmd, msg_cmd = uninstall_cmd_autorun()
        results.append({"path": "HKCU\\Software\\Microsoft\\Command Processor\\AutoRun", "ok": ok_cmd, "message": msg_cmd})

    return results

if __name__ == "__main__":
    data_dir = Path.home() / ".copyterm"
    res = install_all_shell_hooks(data_dir)
    for r in res:
        print(f"[{'OK' if r['ok'] else 'FAIL'}] {r['shell']}: {r['message']} ({r['path']})")

