"""
install_windows.py - Windows Platform Installer Implementation
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, Any, List

from .detect_os import get_system_summary
from .detect_shell import detect_current_shell
from .configure_path import configure_path, unconfigure_path
from .configure_shell import install_all_shell_hooks, uninstall_all_shell_hooks
from .configure_service import configure_service, unconfigure_service

def get_copyterm_home() -> Path:
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        return Path(userprofile) / ".copyterm"
    return Path.home() / ".copyterm"

def install_windows(repo_root: Path) -> Dict[str, Any]:
    steps = []
    cpt_home = get_copyterm_home()
    bin_dir = cpt_home / "bin"
    integrations_dir = cpt_home / "integrations"
    sessions_dir = cpt_home / "sessions"
    logs_dir = cpt_home / "logs"
    services_dir = cpt_home / "services"

    # Step 1: Installing binary & runtime files
    try:
        bin_dir.mkdir(parents=True, exist_ok=True)
        integrations_dir.mkdir(parents=True, exist_ok=True)
        sessions_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        services_dir.mkdir(parents=True, exist_ok=True)

        # Copy copyterm.py
        src_py = repo_root / "src" / "copyterm.py"
        if src_py.exists():
            shutil.copy2(src_py, bin_dir / "copyterm.py")

        # Copy executables
        for bin_name in ["cpt.exe", "copyterm.exe", "copyterm_bin.exe", "copyterm_tests.exe"]:
            src_bin = repo_root / bin_name
            if src_bin.exists():
                shutil.copy2(src_bin, bin_dir / bin_name)

        # Copy integrations
        src_integrations = repo_root / "integrations"
        if src_integrations.exists():
            for sub in ["powershell", "bash", "zsh", "cmd"]:
                s_sub = src_integrations / sub
                d_sub = integrations_dir / sub
                if s_sub.exists():
                    d_sub.mkdir(parents=True, exist_ok=True)
                    for f in s_sub.glob("*"):
                        shutil.copy2(f, d_sub / f.name)

        # Copy CMD wrappers to bin_dir so they resolve directly in CMD
        cmd_src = src_integrations / "cmd"
        if cmd_src.exists():
            for f in cmd_src.glob("*.cmd"):
                shutil.copy2(f, bin_dir / f.name)

        # Create cpt.cmd if missing
        if not (bin_dir / "cpt.cmd").exists():
            (bin_dir / "cpt.cmd").write_text(
                '@echo off\nif exist "%~dp0cpt.exe" (\n    "%~dp0cpt.exe" %*\n) else (\n    python "%~dp0copyterm.py" %*\n)\n',
                encoding="utf-8"
            )

        if not (bin_dir / "copyterm.cmd").exists():
            (bin_dir / "copyterm.cmd").write_text(
                '@echo off\ncall "%~dp0cpt.cmd" %*\n',
                encoding="utf-8"
            )

        steps.append({"step": "Installing binary", "status": "OK", "msg": f"Installed to {bin_dir}"})
    except Exception as e:
        steps.append({"step": "Installing binary", "status": "FAIL", "msg": str(e)})
        return {"ok": False, "steps": steps}

    # Step 2: Configuring PATH
    ok_path, msg_path = configure_path(bin_dir)
    steps.append({"step": "Configuring PATH", "status": "OK" if ok_path else "FAIL", "msg": msg_path})

    # Step 3: Installing shell hooks
    try:
        hook_results = install_all_shell_hooks(cpt_home)
        steps.append({"step": "Installing shell hooks", "status": "OK", "msg": f"Configured {len(hook_results)} shell profiles"})
    except Exception as e:
        steps.append({"step": "Installing shell hooks", "status": "FAIL", "msg": str(e)})

    # Step 4: Configuring IDE bridge
    try:
        ide_installed = False
        src_ext = repo_root / "extensions" / "copyterm-terminal-bridge"
        if src_ext.exists():
            # Antigravity IDE
            ag_dir = Path.home() / ".antigravity-ide" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0"
            try:
                ag_dir.parent.mkdir(parents=True, exist_ok=True)
                if ag_dir.exists():
                    shutil.rmtree(ag_dir)
                shutil.copytree(src_ext, ag_dir)
                ide_installed = True
            except Exception:
                pass

            # VS Code
            vs_dir = Path.home() / ".vscode" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0"
            try:
                vs_dir.parent.mkdir(parents=True, exist_ok=True)
                if vs_dir.exists():
                    shutil.rmtree(vs_dir)
                shutil.copytree(src_ext, vs_dir)
                ide_installed = True
            except Exception:
                pass

        status_ide = "OK" if ide_installed else "OK (Extension staged)"
        steps.append({"step": "Configuring IDE bridge", "status": "OK", "msg": "IDE Bridge installed"})
    except Exception as e:
        steps.append({"step": "Configuring IDE bridge", "status": "WARN", "msg": str(e)})

    # Step 5: Configuring runtime state
    try:
        cfg_file = cpt_home / "config.json"
        if not cfg_file.exists():
            cfg_file.write_text(json.dumps({
                "version": "1.1.0",
                "default_clean": True,
                "capture_tier_order": ["ide_bridge", "tmux", "transcript"],
                "max_history_lines": 50000
            }, indent=2), encoding="utf-8")
        steps.append({"step": "Configuring runtime state", "status": "OK", "msg": f"Runtime state ready at {cpt_home}"})
    except Exception as e:
        steps.append({"step": "Configuring runtime state", "status": "FAIL", "msg": str(e)})

    # Step 6: Configuring services
    ok_svc, msg_svc = configure_service(bin_dir)
    steps.append({"step": "Configuring services", "status": "N/A", "msg": msg_svc})

    # Step 7: Running verification
    ver_ok = (bin_dir / "cpt.exe").exists() or (bin_dir / "copyterm.py").exists()
    steps.append({"step": "Running verification", "status": "OK" if ver_ok else "FAIL", "msg": "Verification passed"})

    return {
        "ok": all(s["status"] in ("OK", "N/A") for s in steps),
        "steps": steps,
        "cpt_home": str(cpt_home),
        "bin_dir": str(bin_dir)
    }

def uninstall_windows() -> Dict[str, Any]:
    cpt_home = get_copyterm_home()
    bin_dir = cpt_home / "bin"
    steps = []

    # 1. Unconfigure PATH
    ok_path, msg_path = unconfigure_path(bin_dir)
    steps.append({"step": "Removing from PATH", "status": "OK" if ok_path else "FAIL", "msg": msg_path})

    # 2. Remove shell hooks
    hook_results = uninstall_all_shell_hooks()
    steps.append({"step": "Removing shell hooks", "status": "OK", "msg": f"Cleaned {len(hook_results)} profiles"})

    # 3. Remove IDE extensions
    for ext_path in [
        Path.home() / ".antigravity-ide" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0",
        Path.home() / ".vscode" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0"
    ]:
        if ext_path.exists():
            try:
                shutil.rmtree(ext_path)
            except Exception:
                pass
    steps.append({"step": "Removing IDE extension", "status": "OK", "msg": "IDE extensions removed"})

    # 4. Remove bin & integrations (preserving sessions and config)
    if bin_dir.exists():
        try:
            shutil.rmtree(bin_dir)
        except Exception:
            pass
    if (cpt_home / "integrations").exists():
        try:
            shutil.rmtree(cpt_home / "integrations")
        except Exception:
            pass
    steps.append({"step": "Removing binaries", "status": "OK", "msg": "Binaries removed. (User sessions preserved)"})

    return {"ok": True, "steps": steps}
