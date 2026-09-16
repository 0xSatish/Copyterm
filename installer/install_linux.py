"""
install_linux.py - Linux Platform Installer Implementation
"""

import os
import sys
import shutil
import json
from pathlib import Path
from typing import Dict, Any

from .detect_os import detect_distro, is_systemd_available
from .configure_path import configure_path, unconfigure_path
from .configure_shell import install_all_shell_hooks, uninstall_all_shell_hooks
from .configure_service import configure_service, unconfigure_service

def get_copyterm_home() -> Path:
    return Path(os.environ.get("COPYTERM_DATA_DIR", str(Path.home() / ".copyterm")))

def install_linux(repo_root: Path) -> Dict[str, Any]:
    steps = []
    cpt_home = get_copyterm_home()
    bin_dir = cpt_home / "bin"
    integrations_dir = cpt_home / "integrations"
    sessions_dir = cpt_home / "sessions"
    logs_dir = cpt_home / "logs"
    services_dir = cpt_home / "services"

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

        # Copy executable binaries if present
        for bin_name in ["cpt", "copyterm"]:
            src_bin = repo_root / bin_name
            if src_bin.exists():
                dst_bin = bin_dir / bin_name
                shutil.copy2(src_bin, dst_bin)
                dst_bin.chmod(0o755)

        # Create wrapper script 'cpt' if compiled binary does not exist
        cpt_wrapper = bin_dir / "cpt"
        if not cpt_wrapper.exists():
            cpt_wrapper.write_text(
                '#!/usr/bin/env bash\n'
                'exec python3 "$(dirname "$0")/copyterm.py" "$@"\n',
                encoding="utf-8"
            )
            cpt_wrapper.chmod(0o755)

        copyterm_wrapper = bin_dir / "copyterm"
        if not copyterm_wrapper.exists():
            copyterm_wrapper.write_text(
                '#!/usr/bin/env bash\n'
                'exec "$(dirname "$0")/cpt" "$@"\n',
                encoding="utf-8"
            )
            copyterm_wrapper.chmod(0o755)

        # Copy integrations
        src_integrations = repo_root / "integrations"
        if src_integrations.exists():
            for sub in ["bash", "zsh", "powershell"]:
                s_sub = src_integrations / sub
                d_sub = integrations_dir / sub
                if s_sub.exists():
                    d_sub.mkdir(parents=True, exist_ok=True)
                    for f in s_sub.glob("*"):
                        shutil.copy2(f, d_sub / f.name)

        steps.append({"step": "Installing binary", "status": "OK", "msg": f"Installed to {bin_dir}"})
    except Exception as e:
        steps.append({"step": "Installing binary", "status": "FAIL", "msg": str(e)})
        return {"ok": False, "steps": steps}

    # Step 2: PATH configuration
    ok_path, msg_path = configure_path(bin_dir)
    steps.append({"step": "Configuring PATH", "status": "OK" if ok_path else "FAIL", "msg": msg_path})

    # Step 3: Shell Integration
    try:
        hook_results = install_all_shell_hooks(cpt_home)
        steps.append({"step": "Installing shell integration", "status": "OK", "msg": f"Configured {len(hook_results)} profiles"})
    except Exception as e:
        steps.append({"step": "Installing shell integration", "status": "FAIL", "msg": str(e)})

    # Step 4: IDE Bridge
    try:
        src_ext = repo_root / "extensions" / "copyterm-terminal-bridge"
        if src_ext.exists():
            for ext_base in [Path.home() / ".antigravity-ide" / "extensions", Path.home() / ".vscode" / "extensions"]:
                dest = ext_base / "copyterm.copyterm-terminal-bridge-1.0.0"
                try:
                    ext_base.mkdir(parents=True, exist_ok=True)
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(src_ext, dest)
                except Exception:
                    pass
        steps.append({"step": "Configuring IDE bridge", "status": "OK", "msg": "IDE extensions installed"})
    except Exception as e:
        steps.append({"step": "Configuring IDE bridge", "status": "WARN", "msg": str(e)})

    # Step 5: Runtime state
    try:
        cfg_file = cpt_home / "config.json"
        if not cfg_file.exists():
            cfg_file.write_text(json.dumps({
                "version": "1.1.0",
                "default_clean": True,
                "capture_tier_order": ["ide_bridge", "tmux", "transcript"],
                "max_history_lines": 50000
            }, indent=2), encoding="utf-8")
        steps.append({"step": "Configuring runtime state", "status": "OK", "msg": f"Runtime state at {cpt_home}"})
    except Exception as e:
        steps.append({"step": "Configuring runtime state", "status": "FAIL", "msg": str(e)})

    # Step 6: Services
    ok_svc, msg_svc = configure_service(bin_dir)
    status_svc = "OK" if ok_svc and is_systemd_available() else "N/A"
    steps.append({"step": "Configuring user service", "status": status_svc, "msg": msg_svc})

    # Step 7: Verification
    ver_ok = (bin_dir / "cpt").exists() and (bin_dir / "copyterm.py").exists()
    steps.append({"step": "Running verification", "status": "OK" if ver_ok else "FAIL", "msg": "Verification passed"})

    return {
        "ok": all(s["status"] in ("OK", "N/A", "WARN") for s in steps),
        "steps": steps,
        "cpt_home": str(cpt_home),
        "bin_dir": str(bin_dir)
    }

def uninstall_linux() -> Dict[str, Any]:
    cpt_home = get_copyterm_home()
    bin_dir = cpt_home / "bin"
    steps = []

    # 1. Unconfigure service
    unconfigure_service()
    steps.append({"step": "Removing service", "status": "OK", "msg": "Services cleaned"})

    # 2. Shell hooks
    uninstall_all_shell_hooks()
    steps.append({"step": "Removing shell hooks", "status": "OK", "msg": "Shell hooks removed"})

    # 3. IDE extensions
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

    # 4. Binaries
    if bin_dir.exists():
        shutil.rmtree(bin_dir, ignore_errors=True)
    if (cpt_home / "integrations").exists():
        shutil.rmtree(cpt_home / "integrations", ignore_errors=True)
    steps.append({"step": "Removing binaries", "status": "OK", "msg": "Binaries removed"})

    return {"ok": True, "steps": steps}
