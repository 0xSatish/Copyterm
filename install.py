#!/usr/bin/env python3
"""
install.py - Universal Cross-Platform Installer for CopyTerm (cpt)
"""

import os
import sys
import argparse
from pathlib import Path

# Add repo root to sys.path so installer package is imported
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from installer.detect_os import detect_os, get_system_summary
from installer.detect_shell import detect_current_shell
from installer.install_windows import install_windows, uninstall_windows
from installer.install_linux import install_linux, uninstall_linux
from installer.install_macos import install_macos, uninstall_macos
from installer.verify_install import run_verification

def print_header(title: str = "CopyTerm Installer"):
    print("\n" + "=" * 50)
    print(f" {title.center(48)} ")
    print("=" * 50 + "\n")

def run_install(args: argparse.Namespace) -> int:
    sys_info = get_system_summary()
    shell_name = detect_current_shell()

    if not args.quiet:
        print_header("CopyTerm Installer")
        print(f"Detected OS       : {sys_info['os_display']}")
        print(f"Architecture      : {sys_info['arch']}")
        print(f"Shell             : {shell_name}")
        print(f"Terminal          : {sys_info['terminal']}")
        print(f"IDE               : {sys_info['ide']}")
        if sys_info['os'] == 'linux':
            print(f"systemd           : {sys_info['systemd']}")
        print("")

    os_type = sys_info['os']
    if os_type == "windows":
        res = install_windows(REPO_ROOT)
    elif os_type == "linux":
        res = install_linux(REPO_ROOT)
    elif os_type == "macos":
        res = install_macos(REPO_ROOT)
    else:
        res = install_linux(REPO_ROOT)

    total_steps = len(res.get("steps", []))
    for i, step in enumerate(res.get("steps", []), 1):
        step_name = f"[{i}/{total_steps}] {step['step']}"
        dots = "." * max(2, (38 - len(step_name)))
        status = step["status"]
        if not args.quiet:
            print(f"{step_name} {dots} {status}")

    if not args.quiet:
        if res.get("ok"):
            print("\n" + "-" * 50)
            print(" CopyTerm installation successful.")
            print("-" * 50)
            print("\nCommand:")
            print("    cpt  (alias: copyterm)")
            print("\nRuntime State:")
            print(f"    {res.get('cpt_home')}")
            print("\nOpen a new terminal before using cpt to ensure the updated PATH is loaded.\n")
        else:
            print("\n" + "!" * 50)
            print(" CopyTerm installation encountered errors.")
            print("!" * 50 + "\n")

    return 0 if res.get("ok") else 1

def run_uninstall(args: argparse.Namespace) -> int:
    sys_info = get_system_summary()
    if not args.quiet:
        print_header("CopyTerm Uninstaller")

    os_type = sys_info['os']
    if os_type == "windows":
        res = uninstall_windows()
    elif os_type == "macos":
        res = uninstall_macos()
    else:
        res = uninstall_linux()

    for i, step in enumerate(res.get("steps", []), 1):
        step_name = f"[{i}/{len(res.get('steps', []))}] {step['step']}"
        dots = "." * max(2, (38 - len(step_name)))
        if not args.quiet:
            print(f"{step_name} {dots} {step['status']}")

    if not args.quiet:
        print("\nCopyTerm uninstallation complete.\n")
    return 0

def main():
    parser = argparse.ArgumentParser(
        prog="install.py",
        description="CopyTerm Universal One-Time Bootstrap Installer"
    )
    parser.add_argument("--uninstall", action="store_true", help="Uninstall CopyTerm from the system")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade CopyTerm installation")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output mode")
    parser.add_argument("--doctor", action="store_true", help="Run diagnostics on existing installation")

    args = parser.parse_args()

    if args.uninstall:
        return run_uninstall(args)

    if args.doctor:
        cpt_home = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".copyterm"
        v = run_verification(cpt_home)
        print_header("CopyTerm Doctor")
        for k, val in v["details"].items():
            print(f"  {k:20}: {val}")
        return 0 if v["ok"] else 1

    return run_install(args)

if __name__ == "__main__":
    sys.exit(main())
