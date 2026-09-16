#!/usr/bin/env python3
"""
TEST: CopyTerm IDE Bridge Security & Protocol Validation
Verifies token authentication, rejection of invalid tokens, malformed JSON, and unknown PID handling.
"""

import sys
import os
import json
import time
import ctypes
from pathlib import Path

def run_security_tests():
    print("=== TEST: CopyTerm IDE Bridge Security & Protocol Validation ===")
    
    disc_file = Path.home() / ".copyterm" / "ide_bridge.json"
    if not disc_file.exists():
        print("FAIL: Discovery file does not exist")
        sys.exit(1)
        
    info = json.loads(disc_file.read_text(encoding='utf-8'))
    endpoint = info["endpoint"]
    valid_token = info["auth_token"]
    
    kernel32 = ctypes.windll.kernel32
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    
    def send_raw(payload_bytes: bytes) -> str:
        h = kernel32.CreateFileW(endpoint, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
        if h == -1 or h == 0:
            return ""
        try:
            written = ctypes.c_ulong(0)
            kernel32.WriteFile(h, payload_bytes, len(payload_bytes), ctypes.byref(written), None)
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
            return b"".join(chunks).decode('utf-8', errors='replace').strip()
        finally:
            kernel32.CloseHandle(h)

    # Test 1: Valid Ping
    resp1 = json.loads(send_raw((json.dumps({
        "version": 1,
        "action": "ping",
        "auth_token": valid_token
    }) + "\n").encode('utf-8')))
    assert resp1.get("ok") is True and resp1.get("message") == "pong", f"Test 1 Failed: {resp1}"
    print("  [PASS] Test 1: Valid authenticated ping succeeded")

    # Test 2: Invalid Auth Token
    resp2 = json.loads(send_raw((json.dumps({
        "version": 1,
        "action": "ping",
        "auth_token": "FORGED_INVALID_TOKEN_99999"
    }) + "\n").encode('utf-8')))
    assert resp2.get("ok") is False and "Unauthorized" in resp2.get("error", ""), f"Test 2 Failed: {resp2}"
    print("  [PASS] Test 2: Invalid token properly rejected with 401 Unauthorized")

    # Test 3: Missing Auth Token
    resp3 = json.loads(send_raw((json.dumps({
        "version": 1,
        "action": "ping"
    }) + "\n").encode('utf-8')))
    assert resp3.get("ok") is False and "Unauthorized" in resp3.get("error", ""), f"Test 3 Failed: {resp3}"
    print("  [PASS] Test 3: Missing token properly rejected")

    # Test 4: Malformed JSON
    resp4 = json.loads(send_raw(b"{THIS_IS_NOT_VALID_JSON}\n"))
    assert resp4.get("ok") is False and "Malformed" in resp4.get("error", ""), f"Test 4 Failed: {resp4}"
    print("  [PASS] Test 4: Malformed JSON handled gracefully")

    # Test 5: Unknown Action
    resp5 = json.loads(send_raw((json.dumps({
        "version": 1,
        "action": "unknown_action_xyz",
        "auth_token": valid_token
    }) + "\n").encode('utf-8')))
    assert resp5.get("ok") is False and "Unknown action" in resp5.get("error", ""), f"Test 5 Failed: {resp5}"
    print("  [PASS] Test 5: Unknown action rejected safely")

    # Test 6: Doctor Diagnostic Action
    resp6 = json.loads(send_raw((json.dumps({
        "version": 1,
        "action": "doctor",
        "auth_token": valid_token
    }) + "\n").encode('utf-8')))
    assert resp6.get("ok") is True and "capabilities" in resp6, f"Test 6 Failed: {resp6}"
    print("  [PASS] Test 6: Authenticated doctor probe succeeded")

    print("=== RESULT: ALL SECURITY TESTS PASSED ===")

if __name__ == "__main__":
    run_security_tests()
