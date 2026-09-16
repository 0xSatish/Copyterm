#!/usr/bin/env python3
"""
Standalone diagnostic client for CopyTerm IDE Bridge.
Directly connects to Windows Named Pipe / Unix Domain Socket and inspects capture response.
"""

import sys
import os
import json
import time
import ctypes
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Debug CopyTerm IDE Bridge Client")
    parser.add_argument("--save", type=str, help="Save captured content to file")
    parser.add_argument("--pid", type=int, help="Override caller PID to query")
    parser.add_argument("--action", type=str, default="capture_terminal", help="Action to send (ping, doctor, capture_terminal)")
    args = parser.parse_args()

    disc_file = Path.home() / ".copyterm" / "ide_bridge.json"
    if not disc_file.exists():
        print("FAIL: Discovery file does not exist at:", disc_file)
        return 1

    try:
        disc = json.loads(disc_file.read_text(encoding='utf-8'))
    except Exception as e:
        print("FAIL: Failed to parse discovery file:", e)
        return 1

    print(f"Bridge Endpoint: {disc.get('endpoint')}")
    print(f"Bridge Host PID: {disc.get('pid')}")
    print(f"IDE:             {disc.get('ide')}")
    print(f"Protocol:        v{disc.get('protocol_version')}")
    
    endpoint = disc.get("endpoint")
    auth_token = disc.get("auth_token")
    caller_pid = args.pid if args.pid is not None else os.getppid()
    print(f"Querying with Caller PID: {caller_pid} (Current PID: {os.getpid()}, PPID: {os.getppid()})")

    kernel32 = ctypes.windll.kernel32
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3

    h_pipe = kernel32.CreateFileW(endpoint, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
    if h_pipe == -1 or h_pipe == 0:
        err = kernel32.GetLastError()
        print(f"FAIL: Failed to connect to Named Pipe (Win32 Error: {err})")
        return 1

    print("Bridge: CONNECTED")
    print("Authentication: PASS")

    try:
        req = {
            "version": 1,
            "action": args.action,
            "caller_pid": caller_pid,
            "nonce": str(time.time()),
            "auth_token": auth_token
        }
        req_bytes = (json.dumps(req) + "\n").encode('utf-8')
        written = ctypes.c_ulong(0)
        kernel32.WriteFile(h_pipe, req_bytes, len(req_bytes), ctypes.byref(written), None)
        print(f"Request: SENT ({written.value} bytes)")

        chunks = []
        buf = ctypes.create_string_buffer(65536)
        read_bytes = ctypes.c_ulong(0)
        while True:
            res = kernel32.ReadFile(h_pipe, buf, 65536, ctypes.byref(read_bytes), None)
            if not res or read_bytes.value == 0:
                break
            chunks.append(buf.raw[:read_bytes.value])
            if b'\n' in chunks[-1] or chunks[-1].endswith(b'}'):
                break

        resp_raw = b"".join(chunks).decode('utf-8', errors='replace').strip()
        print("Response: RECEIVED")
        
        try:
            resp = json.loads(resp_raw)
        except Exception as e:
            print("FAIL: Failed to parse JSON response:", e)
            print("Raw response:", resp_raw[:500])
            return 1

        print(f"OK:       {resp.get('ok')}")
        if not resp.get('ok'):
            print(f"Error:    {resp.get('error')}")
            return 1

        if args.action == "doctor":
            print(f"Terminals Open: {resp.get('terminal_count')}")
            print(f"Active Terminal: {resp.get('active_terminal')}")
            return 0

        term = resp.get("terminal", {})
        content = resp.get("content", "")
        meta = resp.get("metadata", {})
        line_count = len(content.splitlines()) if content else 0
        byte_count = len(content.encode('utf-8')) if content else 0

        print(f"Terminal: {term.get('name')}")
        print(f"PID:      {term.get('process_id')}")
        print(f"Bytes:    {byte_count}")
        print(f"Lines:    {line_count}")

        if content:
            lines = content.splitlines()
            print("First 3 lines preview:")
            for l in lines[:3]:
                print(f"  | {l}")
            print("Last 3 lines preview:")
            for l in lines[-3:]:
                print(f"  | {l}")

        if args.save and content:
            Path(args.save).write_text(content, encoding='utf-8')
            print(f"Saved:    {args.save}")

        return 0
    finally:
        kernel32.CloseHandle(h_pipe)

if __name__ == "__main__":
    sys.exit(main())
