#!/usr/bin/env python3
import sys
import json
import ctypes
from pathlib import Path

disc_file = Path.home() / ".copyterm" / "ide_bridge.json"
disc = json.loads(disc_file.read_text(encoding='utf-8'))
endpoint = disc["endpoint"]
auth_token = disc["auth_token"]

kernel32 = ctypes.windll.kernel32
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3

def query_bridge(action, pid=None):
    h = kernel32.CreateFileW(endpoint, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
    if h == -1 or h == 0:
        return None
    try:
        req = {
            "version": 1,
            "action": action,
            "caller_pids": [pid] if pid else [],
            "caller_pid": pid or 0,
            "auth_token": auth_token
        }
        data = (json.dumps(req) + "\n").encode('utf-8')
        written = ctypes.c_ulong(0)
        kernel32.WriteFile(h, data, len(data), ctypes.byref(written), None)
        buf = ctypes.create_string_buffer(65536)
        read_bytes = ctypes.c_ulong(0)
        chunks = []
        while True:
            res = kernel32.ReadFile(h, buf, 65536, ctypes.byref(read_bytes), None)
            if not res or read_bytes.value == 0:
                break
            chunks.append(buf.raw[:read_bytes.value])
            if b'\n' in chunks[-1] or chunks[-1].endswith(b'}'):
                break
        return json.loads(b"".join(chunks).decode('utf-8', errors='replace').strip())
    finally:
        kernel32.CloseHandle(h)

doc = query_bridge("doctor")
print("Doctor response:", doc.get("ok"))
print("Terminal count:", doc.get("terminal_count"))
for t in doc.get("terminals", []):
    print(f"\n--- Terminal #{t['index']}: {t['name']} (PID: {t['process_id']}, Active: {t['is_active']}) ---")
    if t['process_id']:
        cap = query_bridge("capture_terminal", t['process_id'])
        if cap and cap.get("ok"):
            content = cap.get("content", "")
            lines = content.splitlines()
            print(f"  Captured: {len(lines)} lines, {len(content)} chars")
            for l in lines[:2]:
                print(f"    | {l}")
            if len(lines) > 4:
                print("    | ...")
            for l in lines[-2:]:
                print(f"    | {l}")
        else:
            print("  Capture failed:", cap.get("error") if cap else "No response")
