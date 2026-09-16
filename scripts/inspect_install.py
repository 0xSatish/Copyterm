import os
import sys
import winreg
from pathlib import Path

print("=== INSPECTING COPYTERM ENVIRONMENT ===")

# 1. Check ~/.copyterm
cpt_home = Path(os.environ.get("USERPROFILE", "")) / ".copyterm"
print(f"CopyTerm Home: {cpt_home} (exists={cpt_home.exists()})")
if cpt_home.exists():
    for f in cpt_home.rglob("*"):
        if f.is_file():
            print(f"  File: {f.relative_to(cpt_home)} ({f.stat().st_size} bytes)")

# 2. Check PowerShell Profiles
docs = [
    Path.home() / "Documents",
    Path(os.environ.get("USERPROFILE", "")) / "Documents",
    Path.home() / "OneDrive" / "Documents",
    Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Documents",
]

for d in docs:
    for sub in ["WindowsPowerShell", "PowerShell"]:
        for name in ["Microsoft.PowerShell_profile.ps1", "profile.ps1"]:
            p = d / sub / name
            if p.exists():
                print(f"\n--- Profile Found: {p} ---")
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                    print(content)
                except Exception as e:
                    print(f"Error reading {p}: {e}")

# 3. Check Registry AutoRun
print("\n--- Registry CMD AutoRun ---")
try:
    key_path = r"Software\Microsoft\Command Processor"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
        try:
            val, typ = winreg.QueryValueEx(key, "AutoRun")
            print(f"HKCU\\{key_path}\\AutoRun = {val!r} (type={typ})")
        except FileNotFoundError:
            print(f"HKCU\\{key_path}\\AutoRun not found")
except Exception as e:
    print(f"Registry query error: {e}")
