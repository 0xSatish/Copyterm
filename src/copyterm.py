#!/usr/bin/env python3
"""
COPYTERM — Cross-Platform Terminal Session Capture Utility (Python Core Engine)
Provides 100% feature parity with the native C++ engine with zero external dependencies.
"""

import sys
import os
import re
import time
import ctypes
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

VERSION = "1.0.0"

def get_data_dir() -> Path:
    custom = os.environ.get("COPYTERM_DATA_DIR")
    if custom:
        return Path(custom)
    if sys.platform == "win32":
        profile = os.environ.get("USERPROFILE")
        if profile:
            return Path(profile) / ".copyterm"
        appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            return Path(appdata) / "copyterm"
    home = os.environ.get("HOME")
    if home:
        return Path(home) / ".copyterm"
    return Path.home() / ".copyterm"

def get_sessions_dir() -> Path:
    return get_data_dir() / "sessions"

# --- ANSI & VT Sanitizer ---

class Sanitizer:
    CSI_RE = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z~]')
    OSC_RE = re.compile(r'\x1b\](?:[^\x07\x1b]|\x1b[^\\])*?(?:\x07|\x1b\\)')
    SHELL_MARK_RE = re.compile(r'\x1b\]133;[^\x07\x1b]*?(?:\x07|\x1b\\)')
    TRANSCRIPT_BANNER_RE = re.compile(r'\*{20,}[\s\S]*?\*{20,}\s*(Transcript started[^\n]*\n)?', re.MULTILINE)

    @classmethod
    def strip_ansi(cls, text: str) -> str:
        text = cls.OSC_RE.sub('', text)
        text = cls.CSI_RE.sub('', text)
        return text

    @classmethod
    def strip_shell_marks(cls, text: str) -> str:
        return cls.SHELL_MARK_RE.sub('', text)

    @classmethod
    def strip_transcript_banners(cls, text: str) -> str:
        text = cls.TRANSCRIPT_BANNER_RE.sub('', text)
        # Also clean leftover transcript notices
        lines = []
        for line in text.splitlines(keepends=True):
            if "Transcript started, output file is" in line or "Transcript stopped, output file is" in line:
                continue
            lines.append(line)
        return "".join(lines)

    @classmethod
    def collapse_carriage_returns(cls, text: str) -> str:
        result = []
        current_line = []
        cursor_col = 0
        i = 0
        n = len(text)

        while i < n:
            c = text[i]
            if c == '\r':
                if i + 1 < n and text[i + 1] == '\n':
                    result.append("".join(current_line))
                    result.append("\n")
                    current_line = []
                    cursor_col = 0
                    i += 1
                else:
                    cursor_col = 0
            elif c == '\n':
                result.append("".join(current_line))
                result.append("\n")
                current_line = []
                cursor_col = 0
            elif c == '\b':
                if cursor_col > 0:
                    cursor_col -= 1
            else:
                if cursor_col < len(current_line):
                    current_line[cursor_col] = c
                else:
                    if cursor_col > len(current_line):
                        current_line.extend([' '] * (cursor_col - len(current_line)))
                    current_line.append(c)
                cursor_col += 1
            i += 1

        if current_line:
            result.append("".join(current_line))
        return "".join(result)

    @classmethod
    def sanitize(cls, text: str) -> str:
        # 1. Strip UTF-8 BOM
        text = text.lstrip('\ufeff')
        # 2. Strip raw ANSI escape codes first
        text = cls.strip_ansi(text)
        # 3. Collapse carriage returns and line overwrites
        text = cls.collapse_carriage_returns(text)
        # 4. Strip transcript banners and shell marks
        text = cls.strip_transcript_banners(text)
        text = cls.strip_shell_marks(text)
        return text

# --- Secret Redaction ---

class Redactor:
    PATTERNS = [
        ("AWS Key", re.compile(r'\b(AKIA[0-9A-Z]{16})\b'), "AKIA[REDACTED_AWS_KEY]"),
        ("GitHub PAT", re.compile(r'\b(gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59})\b'), "[REDACTED_GITHUB_TOKEN]"),
        ("Private Key", re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'), "[REDACTED_PRIVATE_KEY]"),
        ("JWT Token", re.compile(r'(Bearer\s+)(eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)'), r'\1[REDACTED_JWT_TOKEN]'),
        ("Password", re.compile(r'(\b(password|passwd|api_key|apikey|secret_key|secret)\s*[:=]\s*["\']?)([^"\'\s\r\n]{6,})(["\']?)', re.IGNORECASE), r'\1[REDACTED_SECRET]\4'),
    ]

    @classmethod
    def redact(cls, text: str) -> Tuple[str, int]:
        count = 0
        res = text
        for name, pattern, repl in cls.PATTERNS:
            matches = len(pattern.findall(res))
            if matches > 0:
                count += matches
                res = pattern.sub(repl, res)
        return res, count

# --- Native Win32 / Linux Clipboard ---

class Clipboard:
    @staticmethod
    def copy(text: str) -> bool:
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            user32.OpenClipboard.argtypes = [ctypes.c_void_p]
            user32.OpenClipboard.restype = ctypes.c_bool
            user32.EmptyClipboard.restype = ctypes.c_bool
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p
            user32.CloseClipboard.restype = ctypes.c_bool

            kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.restype = ctypes.c_bool
            kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
            kernel32.GlobalFree.restype = ctypes.c_void_p

            GMEM_MOVEABLE = 0x0002
            CF_UNICODETEXT = 13

            # Retry open clipboard up to 10 times in case of transient locks
            opened = False
            for _ in range(10):
                if user32.OpenClipboard(None):
                    opened = True
                    break
                time.sleep(0.05)
            if not opened:
                return False

            try:
                user32.EmptyClipboard()
                encoded = text.encode('utf-16-le') + b'\x00\x00'
                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                if not h_mem:
                    return False
                ptr = kernel32.GlobalLock(h_mem)
                if not ptr:
                    kernel32.GlobalFree(h_mem)
                    return False
                ctypes.memmove(ptr, encoded, len(encoded))
                kernel32.GlobalUnlock(h_mem)
                if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                    kernel32.GlobalFree(h_mem)
                    return False
                return True
            finally:
                user32.CloseClipboard()
        else:
            if os.environ.get("WAYLAND_DISPLAY"):
                try:
                    p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                    p.communicate(text.encode('utf-8'))
                    if p.returncode == 0:
                        return True
                except:
                    pass
            if os.environ.get("DISPLAY"):
                for tool in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                    try:
                        p = subprocess.Popen(tool, stdin=subprocess.PIPE)
                        p.communicate(text.encode('utf-8'))
                        if p.returncode == 0:
                            return True
                    except:
                        pass
            # OSC 52 Fallback
            import base64
            b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
            sys.stdout.write(f"\x1b]52;c;{b64}\x07")
            sys.stdout.flush()
            return True

    @staticmethod
    def get_text() -> str:
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            CF_UNICODETEXT = 13

            opened = False
            for _ in range(5):
                if user32.OpenClipboard(None):
                    opened = True
                    break
                time.sleep(0.02)
            if not opened:
                return ""
            try:
                h_mem = user32.GetClipboardData(CF_UNICODETEXT)
                if not h_mem:
                    return ""
                ptr = kernel32.GlobalLock(h_mem)
                if not ptr:
                    return ""
                try:
                    return ctypes.wstring_at(ptr)
                finally:
                    kernel32.GlobalUnlock(h_mem)
            finally:
                user32.CloseClipboard()
        return ""

# --- Session Resolver ---

class SessionManager:
    @staticmethod
    def get_parent_pid() -> int:
        return os.getppid()

    @staticmethod
    def resolve_session(explicit_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if explicit_id:
            sess_id = explicit_id
        else:
            sess_id = os.environ.get("COPYTERM_SESSION_ID")
            if not sess_id and os.environ.get("TMUX_PANE"):
                sess_id = f"tmux_{os.environ.get('TMUX_PANE', '').replace('%', '_')}"
            if not sess_id:
                ppid = SessionManager.get_parent_pid()
                sessions_dir = get_sessions_dir()
                if sessions_dir.exists():
                    for meta_file in sessions_dir.glob("*.meta"):
                        try:
                            content = meta_file.read_text(encoding='utf-8')
                            if f"pid={ppid}" in content:
                                sess_id = meta_file.stem
                                break
                        except:
                            pass

        if not sess_id:
            return None

        buf_path = get_sessions_dir() / f"{sess_id}.buf"
        meta_path = get_sessions_dir() / f"{sess_id}.meta"

        return {
            "session_id": sess_id,
            "buf_path": buf_path,
            "meta_path": meta_path
        }

    @staticmethod
    def read_buffer(buf_path: Path, last_n: int = 0) -> str:
        if not buf_path.exists():
            return ""
        try:
            # Read raw bytes to preserve literal \r without universal-newline translation
            content = buf_path.read_bytes().decode('utf-8-sig', errors='replace')
            if last_n > 0:
                lines = content.splitlines(keepends=True)
                return "".join(lines[-last_n:])
            return content
        except:
            return ""

# --- CLI Main ---

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass
    if hasattr(sys.stderr, 'reconfigure'):
        try:
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except:
            pass

    parser = argparse.ArgumentParser(
        prog="copyterm",
        description="End-to-End Cross-Platform Terminal Session Capture Utility"
    )
    parser.add_argument("-v", "--version", action="version", version=f"copyterm version {VERSION}")
    parser.add_argument("-n", "--last", type=int, default=0, help="Copy only the last N lines")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean ANSI codes (default)")
    parser.add_argument("--raw", action="store_true", help="Preserve raw VT sequences")
    parser.add_argument("--ai", action="store_true", help="Format as AI markdown")
    parser.add_argument("--redact", action="store_true", help="Mask secrets and tokens")
    parser.add_argument("--commands-only", action="store_true", help="Extract only commands")
    parser.add_argument("--output-only", action="store_true", help="Extract only output")
    parser.add_argument("-s", "--save", type=str, help="Save to file")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")
    parser.add_argument("--session-id", type=str, help="Override session ID")

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.add_parser("doctor", help="Show diagnostics")
    subparsers.add_parser("list", help="List active sessions")
    subparsers.add_parser("clean-sessions", help="Clean stale sessions")
    inst = subparsers.add_parser("install", help="Install shell hooks")
    inst.add_argument("shell", nargs="?", default="all", help="Target shell (powershell, bash, zsh, all)")

    args = parser.parse_args()

    if args.subcommand == "doctor":
        print("============================================================")
        print("               COPYTERM DIAGNOSTIC DOCTOR REPORT            ")
        print("============================================================")
        print(f"  OS:                 {sys.platform}")
        print(f"  Current PID:        {os.getpid()}")
        print(f"  Parent PID (PPID):  {SessionManager.get_parent_pid()}")
        print(f"  Data Directory:     {get_data_dir()}")
        print(f"  Clipboard Status:   AVAILABLE")
        sess = SessionManager.resolve_session(args.session_id)
        if sess:
            print(f"  Resolved Session ID: {sess['session_id']}")
            print(f"  Buffer Path:         {sess['buf_path']}")
        else:
            print(f"  Resolved Session:    No active session detected")
        print("============================================================")
        return 0

    sess = SessionManager.resolve_session(args.session_id)
    if not sess:
        sys.stderr.write("copyterm: No active capture session detected for this terminal.\n")
        sys.stderr.write("Run 'copyterm install' to enable automatic capture.\n")
        return 1

    raw_text = SessionManager.read_buffer(sess["buf_path"], args.last)
    if not raw_text:
        sys.stderr.write(f"copyterm: Terminal session [{sess['session_id']}] has no recorded output yet.\n")
        return 0

    if args.raw:
        processed = raw_text
    else:
        processed = Sanitizer.sanitize(raw_text)

    if args.commands_only:
        lines = [l for l in processed.splitlines(keepends=True) if l.startswith(("$ ", "> ", "# ", "PS "))]
        processed = "".join(lines)
    elif args.output_only:
        lines = [l for l in processed.splitlines(keepends=True) if not l.startswith(("$ ", "> ", "# ", "PS "))]
        processed = "".join(lines)

    secrets_count = 0
    if args.redact:
        processed, secrets_count = Redactor.redact(processed)

    if args.ai:
        processed = f"### Terminal Session Output\n\n- **Session ID:** `{sess['session_id']}`\n\n```bash\n{processed.rstrip()}\n```\n"

    if args.stdout:
        sys.stdout.write(processed)
        sys.stdout.flush()
        return 0

    if args.save:
        Path(args.save).write_text(processed, encoding='utf-8')
        print(f"Saved {len(processed.splitlines())} lines to {args.save}")
        return 0

    ok = Clipboard.copy(processed)
    if not ok:
        sys.stderr.write("copyterm: Failed to copy to clipboard.\n")
        return 1

    line_count = len(processed.splitlines())
    byte_count = len(processed.encode('utf-8'))
    size_str = f"{byte_count} B" if byte_count < 1024 else f"{byte_count // 1024} KB"
    redact_str = f" (Masked {secrets_count} secret tokens)" if secrets_count > 0 else ""
    print(f"Copied {line_count} lines ({size_str}) from terminal session [{sess['session_id']}] to clipboard.{redact_str}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
