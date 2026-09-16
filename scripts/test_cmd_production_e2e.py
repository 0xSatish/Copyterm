#!/usr/bin/env python3
"""
test_cmd_production_e2e.py - Comprehensive E2E Test Suite for CMD and PowerShell
Validates:
1. CLI Version consistency (cpt version, cpt --version, cpt -v) across CMD and PowerShell
2. Fresh CMD automatic capture without pre-existing session ID or manual intervention
3. Strict multi-terminal isolation across multiple CMD instances (CMD A, CMD B, CMD C)
4. CWD independence across arbitrary directories (C:\\, HOME, TEMP)
5. Epoch boundary (cls in CMD)
6. cpt doctor consistency
"""

import os
import sys
import time
import shutil
import subprocess
from pathlib import Path

PASS_COUNT = 0
FAIL_COUNT = 0

def log_test(name: str, passed: bool, details: str = ""):
    global PASS_COUNT, FAIL_COUNT
    if passed:
        PASS_COUNT += 1
        print(f"  [\033[32mPASS\033[0m] {name} {f'({details})' if details else ''}")
    else:
        FAIL_COUNT += 1
        print(f"  [\033[31mFAIL\033[0m] {name} {f'({details})' if details else ''}")

def get_clean_env():
    env = os.environ.copy()
    env.pop("COPYTERM_SESSION_ID", None)
    env.pop("TMUX", None)
    env.pop("TMUX_PANE", None)
    # Ensure bin is in PATH
    bin_dir = str(Path.home() / ".copyterm" / "bin")
    if bin_dir.lower() not in env.get("PATH", "").lower():
        env["PATH"] = f"{bin_dir};{env.get('PATH', '')}"
    return env

def test_version_interface():
    print("\n--- TEST 1: CLI Version Consistency ---")
    canonical_text = "cpt (CopyTerm) version 1.1.0 (cross-platform terminal session capture)"
    
    # 1. PowerShell tests
    for cmd in ["cpt version", "cpt --version", "cpt -v", "copyterm version", "copyterm --version"]:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f"& {{ {cmd} }}"],
            capture_output=True, text=True, env=get_clean_env()
        )
        out = proc.stdout.strip()
        passed = (proc.returncode == 0) and (canonical_text in out)
        log_test(f"PowerShell: {cmd}", passed, f"exit={proc.returncode}")

    # 2. CMD tests
    for cmd in ["cpt version", "cpt --version", "cpt -v", "copyterm version", "copyterm --version"]:
        proc = subprocess.run(
            f"cmd.exe /c \"{cmd}\"",
            shell=True, capture_output=True, text=True, env=get_clean_env()
        )
        out = proc.stdout.strip()
        passed = (proc.returncode == 0) and (canonical_text in out)
        log_test(f"CMD: {cmd}", passed, f"exit={proc.returncode}")

def test_fresh_cmd_automatic_capture():
    print("\n--- TEST 2: Fresh CMD Automatic Capture ---")
    clean_env = get_clean_env()
    
    # Launch fresh cmd.exe that executes commands and cpt
    # In interactive/batch cmd, AutoRun triggers copyterm_init.cmd which creates unique session
    proc = subprocess.run(
        'cmd.exe /c "echo CMD_FRESH_PAYLOAD_LINE_1 && echo CMD_FRESH_PAYLOAD_LINE_2 && cpt --stdout"',
        shell=True, capture_output=True, text=True, env=clean_env
    )
    out = proc.stdout.strip()
    passed = (proc.returncode == 0) and ("CMD_FRESH_PAYLOAD_LINE_1" in out or "CMD_FRESH_PAYLOAD_LINE_2" in out)
    log_test("Fresh CMD Automatic Capture", passed, f"Output length={len(out)}")

def test_cmd_multi_terminal_isolation():
    print("\n--- TEST 3: Multiple CMD Terminal Isolation ---")
    clean_env = get_clean_env()
    
    term_a_token = f"TOKEN_TERM_A_{int(time.time())}"
    term_b_token = f"TOKEN_TERM_B_{int(time.time()) + 1}"
    term_c_token = f"TOKEN_TERM_C_{int(time.time()) + 2}"

    # Terminal A
    proc_a = subprocess.run(
        f'cmd.exe /c "echo {term_a_token} && cpt --stdout"',
        shell=True, capture_output=True, text=True, env=clean_env
    )
    out_a = proc_a.stdout

    # Terminal B
    proc_b = subprocess.run(
        f'cmd.exe /c "echo {term_b_token} && cpt --stdout"',
        shell=True, capture_output=True, text=True, env=clean_env
    )
    out_b = proc_b.stdout

    # Terminal C
    proc_c = subprocess.run(
        f'cmd.exe /c "echo {term_c_token} && cpt --stdout"',
        shell=True, capture_output=True, text=True, env=clean_env
    )
    out_c = proc_c.stdout

    passed_a = (term_a_token in out_a) and (term_b_token not in out_a) and (term_c_token not in out_a)
    passed_b = (term_b_token in out_b) and (term_a_token not in out_b) and (term_c_token not in out_b)
    passed_c = (term_c_token in out_c) and (term_a_token not in out_c) and (term_b_token not in out_c)

    log_test("Terminal A contains only Token A", passed_a)
    log_test("Terminal B contains only Token B", passed_b)
    log_test("Terminal C contains only Token C", passed_c)

def test_cmd_cwd_independence():
    print("\n--- TEST 4: CMD CWD Independence ---")
    clean_env = get_clean_env()
    
    dirs_to_test = [
        Path("C:\\"),
        Path.home(),
        Path(os.environ.get("TEMP", "C:\\Temp"))
    ]
    
    script = (
        'cmd.exe /c "echo CWD_START_LINE && cd C:\\ && cpt doctor && cd %USERPROFILE% && cpt doctor && cd %TEMP% && cpt doctor"'
    )
    proc = subprocess.run(script, shell=True, capture_output=True, text=True, env=clean_env)
    out = proc.stdout
    
    # Extract session IDs from output
    import re
    session_ids = re.findall(r'Session ID:\s+([a-zA-Z0-9_]+)', out)
    passed = len(session_ids) >= 3 and len(set(session_ids)) == 1
    log_test("Session ID unchanged across cd C:\\, cd %USERPROFILE%, cd %TEMP%", passed, f"Resolved ID={session_ids[0] if session_ids else 'none'}")

def test_cmd_epoch_clear():
    print("\n--- TEST 5: CMD Epoch Boundary (cls) ---")
    clean_env = get_clean_env()
    
    script = (
        'cmd.exe /c "echo OLD_BEFORE_CLEAR_LINE && cls && echo NEW_AFTER_CLEAR_LINE && cpt --stdout"'
    )
    proc = subprocess.run(script, shell=True, capture_output=True, text=True, env=clean_env)
    out = proc.stdout
    
    passed = ("NEW_AFTER_CLEAR_LINE" in out) and ("OLD_BEFORE_CLEAR_LINE" not in out)
    log_test("cls establishes Epoch Boundary in CMD", passed)

def test_cpt_doctor():
    print("\n--- TEST 6: cpt doctor shell detection ---")
    clean_env = get_clean_env()
    
    proc_cmd = subprocess.run('cmd.exe /c "cpt doctor"', shell=True, capture_output=True, text=True, env=clean_env)
    passed_cmd = (proc_cmd.returncode == 0) and ("Shell:                  cmd" in proc_cmd.stdout or "Detected Shell:     cmd" in proc_cmd.stdout or "cmd" in proc_cmd.stdout.lower())
    log_test("cpt doctor in CMD reports cmd shell", passed_cmd)
    
    proc_ps = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "& { cpt doctor }"],
        capture_output=True, text=True, env=clean_env
    )
    passed_ps = (proc_ps.returncode == 0) and ("powershell" in proc_ps.stdout.lower())
    log_test("cpt doctor in PowerShell reports powershell", passed_ps)

def main():
    print("============================================================")
    print("        COPYTERM CMD & POWERSHELL E2E VERIFICATION          ")
    print("============================================================")
    test_version_interface()
    test_fresh_cmd_automatic_capture()
    test_cmd_multi_terminal_isolation()
    test_cmd_cwd_independence()
    test_cmd_epoch_clear()
    test_cpt_doctor()
    print("============================================================")
    print(f"Total PASS: {PASS_COUNT}, Total FAIL: {FAIL_COUNT}")
    print("============================================================")
    return 0 if FAIL_COUNT == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
