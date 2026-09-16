"""
verify_install.py - Post-installation Verification & Diagnostics
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def run_verification(cpt_home: Path) -> Dict[str, Any]:
    bin_dir = cpt_home / "bin"
    results = {}

    # 1. Binary check
    has_bin = False
    for b in ["cpt.exe", "cpt", "copyterm.py"]:
        if (bin_dir / b).exists():
            has_bin = True
            break
    results["binary"] = "OK" if has_bin else "FAIL"

    # 2. PATH check
    in_path = False
    bin_str = str(bin_dir.resolve()).lower()
    path_env = os.environ.get("PATH", "").split(os.pathsep)
    for p in path_env:
        if p.strip().lower().rstrip("\\/") == bin_str.rstrip("\\/"):
            in_path = True
            break
    # Also check which
    if not in_path:
        if shutil.which("cpt") or shutil.which("cpt.exe"):
            in_path = True
    results["path"] = "OK" if in_path else "WARN (Restart terminal to refresh PATH)"

    # 3. Shell integrations check
    integrations = cpt_home / "integrations"
    has_integrations = integrations.exists() and any(integrations.iterdir())
    results["shell_integration"] = "OK" if has_integrations else "WARN"

    # 4. State directory check
    sessions = cpt_home / "sessions"
    results["runtime_state"] = "OK" if sessions.exists() else "FAIL"

    # 5. CLI Test execution
    cpt_exe = bin_dir / ("cpt.exe" if sys.platform == "win32" else "cpt")
    cpt_py = bin_dir / "copyterm.py"
    cmd = None
    if cpt_exe.exists():
        cmd = [str(cpt_exe), "--version"]
    elif cpt_py.exists():
        cmd = [sys.executable, str(cpt_py), "--version"]

    if cmd:
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            results["cli_execution"] = "OK" if p.returncode == 0 else f"FAIL ({p.stderr.strip()})"
        except Exception as e:
            results["cli_execution"] = f"FAIL ({e})"
    else:
        results["cli_execution"] = "FAIL (No binary found)"

    all_passed = results["binary"] == "OK" and results["runtime_state"] == "OK"
    return {
        "ok": all_passed,
        "details": results
    }

if __name__ == "__main__":
    home = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".copyterm"
    print(run_verification(home))
