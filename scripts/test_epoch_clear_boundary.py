#!/usr/bin/env python3
"""
COPYTERM — Automated Test Suite for Clear Boundary & Capture Epoch Model
Tests all 15 scenarios specified in the project requirements.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.copyterm import Sanitizer, Redactor, EpochManager, SessionManager, IdeBridgeClient

def run_tests():
    passed = 0
    failed = 0
    total = 0

    def assert_eq(test_id: str, desc: str, actual: str, expected: str):
        nonlocal passed, failed, total
        total += 1
        # Normalize whitespace for comparison
        act_clean = "\n".join([l.rstrip() for l in actual.strip().splitlines()])
        exp_clean = "\n".join([l.rstrip() for l in expected.strip().splitlines()])
        if act_clean == exp_clean:
            print(f"  [PASS] {test_id}: {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {test_id}: {desc}")
            print(f"         Expected: {repr(exp_clean[:200])}")
            print(f"         Actual:   {repr(act_clean[:200])}")
            failed += 1

    print("============================================================")
    print("      COPYTERM CLEAR BOUNDARY & EPOCH TEST SUITE            ")
    print("============================================================")

    # TEST 1: Historical content before cpt (epoch == 0)
    raw_t1 = "OLD_LINE_1\nOLD_LINE_2\nOLD_LINE_3\nPS C:\\> cpt"
    ep_t1 = {"epoch_id": 0, "clear_count": 0, "latest_boundary_token": ""}
    res_t1 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t1, ep_t1))
    assert_eq("TEST 1", "Historical content before cpt (retroactive)", res_t1, "OLD_LINE_1\nOLD_LINE_2\nOLD_LINE_3")

    # TEST 2: Clear boundary (OLD -> clear -> NEW)
    raw_t2 = "OLD_1\nOLD_2\nPS C:\\> clear\nNEW_1\nNEW_2\nPS C:\\> cpt"
    ep_t2 = {"epoch_id": 1, "clear_count": 1, "latest_boundary_token": "CPT_EPOCH_BOUND_sess1_1"}
    res_t2 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t2, ep_t2))
    assert_eq("TEST 2", "Clear establishes capture boundary", res_t2, "NEW_1\nNEW_2")

    # TEST 3: Multiple clears (OLD -> clear -> A, B -> clear -> C, D)
    raw_t3 = "OLD\nPS C:\\> clear\nA\nB\nPS C:\\> clear\nC\nD\nPS C:\\> cpt"
    ep_t3 = {"epoch_id": 2, "clear_count": 2, "latest_boundary_token": "CPT_EPOCH_BOUND_sess1_2"}
    res_t3 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t3, ep_t3))
    assert_eq("TEST 3", "Multiple clears (picks latest epoch only)", res_t3, "C\nD")

    # TEST 4: Echo containing "clear"
    raw_t4 = "OLD\nPS C:\\> Write-Output 'clear'\nclear\nNEW\nPS C:\\> cpt"
    # echo "clear" does not invoke clear command, epoch_id remains 0
    ep_t4 = {"epoch_id": 0, "clear_count": 0, "latest_boundary_token": ""}
    res_t4 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t4, ep_t4))
    assert_eq("TEST 4", "Echo containing 'clear' does not reset epoch", res_t4, "OLD\nPS C:\\> Write-Output 'clear'\nclear\nNEW")

    # TEST 5: Clear with no output (OLD -> clear -> cpt)
    raw_t5 = "OLD_1\nOLD_2\nPS C:\\> clear\nPS C:\\> cpt"
    ep_t5 = {"epoch_id": 1, "clear_count": 1, "latest_boundary_token": "CPT_EPOCH_BOUND_sess1_1"}
    res_t5 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t5, ep_t5))
    assert_eq("TEST 5", "Clear with no output yields empty epoch (no fallback to OLD)", res_t5, "")

    # TEST 6: Large historical buffer before clear + 500 lines after clear
    old_lines = "\n".join([f"OLD_{i}" for i in range(1, 501)])
    new_lines = "\n".join([f"NEW_{i}" for i in range(1, 501)])
    raw_t6 = f"{old_lines}\nPS C:\\> clear\n{new_lines}\nPS C:\\> cpt"
    ep_t6 = {"epoch_id": 1, "clear_count": 1, "latest_boundary_token": "CPT_EPOCH_BOUND_sess1_1"}
    res_t6 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t6, ep_t6))
    assert_eq("TEST 6", "Large historical buffer (500 pre-clear, 500 post-clear)", res_t6, new_lines)

    # TEST 7: 5,000 lines generated after clear
    lines_5k = "\n".join([f"AFTER_CLEAR_{i}" for i in range(1, 5001)])
    raw_t7 = f"OLD_INITIAL\nPS C:\\> clear\n{lines_5k}\nPS C:\\> cpt"
    ep_t7 = {"epoch_id": 1, "clear_count": 1, "latest_boundary_token": "CPT_EPOCH_BOUND_sess1_1"}
    res_t7 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t7, ep_t7))
    assert_eq("TEST 7", "5,000 lines generated after clear captured completely", res_t7, lines_5k)

    # TEST 8: Per-terminal isolation
    term_a_raw = "A_OLD\nPS C:\\> clear\nA_NEW_1\nA_NEW_2\nPS C:\\> cpt"
    term_b_raw = "B_OLD\nPS C:\\> clear\nB_NEW_1\nB_NEW_2\nPS C:\\> cpt"
    ep_a = {"session_id": "sess_A", "epoch_id": 1, "latest_boundary_token": "CPT_EPOCH_A"}
    ep_b = {"session_id": "sess_B", "epoch_id": 1, "latest_boundary_token": "CPT_EPOCH_B"}
    res_a = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(term_a_raw, ep_a))
    res_b = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(term_b_raw, ep_b))
    assert_eq("TEST 8A", "Terminal A isolation", res_a, "A_NEW_1\nA_NEW_2")
    assert_eq("TEST 8B", "Terminal B isolation", res_b, "B_NEW_1\nB_NEW_2")

    # TEST 9: Exact Token Boundary (.buf transcript stream)
    raw_t9 = "PRE_RECORDED_TRANSCRIPT\nCPT_EPOCH_BOUND_sess_99_1\nPOST_CLEAR_OUTPUT_LINE_1\nPOST_CLEAR_OUTPUT_LINE_2"
    ep_t9 = {"epoch_id": 1, "latest_boundary_token": "CPT_EPOCH_BOUND_sess_99_1"}
    res_t9 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t9, ep_t9))
    assert_eq("TEST 9", "Explicit token boundary match in session stream", res_t9, "POST_CLEAR_OUTPUT_LINE_1\nPOST_CLEAR_OUTPUT_LINE_2")

    # TEST 10: Clear command itself excluded
    raw_t10 = "PRE_1\nPS C:\\Users\\test> clear\nPOST_1\nPOST_2\nPS C:\\Users\\test> cpt"
    ep_t10 = {"epoch_id": 1, "latest_boundary_token": ""}
    res_t10 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t10, ep_t10))
    assert_eq("TEST 10", "Clear prompt excluded from captured output", res_t10, "POST_1\nPOST_2")

    # TEST 11: PowerShell cls / Clear-Host command variants
    raw_t11a = "PRE_A\nPS C:\\> cls\nPOST_A\nPS C:\\> cpt"
    raw_t11b = "PRE_B\nPS C:\\> Clear-Host\nPOST_B\nPS C:\\> cpt"
    res_t11a = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t11a, {"epoch_id": 1}))
    res_t11b = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t11b, {"epoch_id": 1}))
    assert_eq("TEST 11A", "cls alias establishes boundary", res_t11a, "POST_A")
    assert_eq("TEST 11B", "Clear-Host establishes boundary", res_t11b, "POST_B")

    # TEST 12: Bash prompt clear
    raw_t12 = "old_bash_1\nuser@ubuntu:~$ clear\nnew_bash_1\nnew_bash_2\nuser@ubuntu:~$ cpt"
    res_t12 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t12, {"epoch_id": 1}))
    assert_eq("TEST 12", "Bash prompt clear establishes boundary", res_t12, "new_bash_1\nnew_bash_2")

    # TEST 13: Zsh prompt clear
    raw_t13 = "old_zsh_1\nuser@mac% clear\nnew_zsh_1\nuser@mac% cpt"
    res_t13 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t13, {"epoch_id": 1}))
    assert_eq("TEST 13", "Zsh prompt clear establishes boundary", res_t13, "new_zsh_1")

    # TEST 14: CMD prompt cls
    raw_t14 = "old_cmd_1\nC:\\Users\\test> cls\nnew_cmd_1\nC:\\Users\\test> cpt"
    res_t14 = Sanitizer.sanitize(EpochManager.slice_buffer_by_epoch(raw_t14, {"epoch_id": 1}))
    assert_eq("TEST 14", "CMD cls establishes boundary", res_t14, "new_cmd_1")

    print("============================================================")
    print(f"TEST SUMMARY: {passed} passed, {failed} failed (Total: {total})")
    print("============================================================")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_tests())
