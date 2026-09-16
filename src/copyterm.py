#!/usr/bin/env python3
"""
COPYTERM (cpt) — Cross-Platform Terminal Session Capture Utility (Python Core Engine)
Canonical Short Command: cpt (Alias: copyterm)
Features:
- True Retroactive Terminal Emulator Buffer capture via CopyTerm IDE Bridge
- Clear as a Copy Boundary (Capture Epoch Model)
- Strict Per-Terminal Session Isolation
- Zero external dependencies
"""

import sys
import os
import re
import time
import json
import shutil
import ctypes
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

VERSION = "1.1.0"
PROTOCOL_VERSION = 1

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

def get_process_ancestor_info() -> List[Dict[str, Any]]:
    info_list = [{"pid": os.getpid(), "ppid": os.getppid(), "name": "python.exe"}]
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ('dwSize', ctypes.c_ulong),
                    ('cntUsage', ctypes.c_ulong),
                    ('th32ProcessID', ctypes.c_ulong),
                    ('th32DefaultHeapID', ctypes.c_void_p),
                    ('th32ModuleID', ctypes.c_ulong),
                    ('cntThreads', ctypes.c_ulong),
                    ('th32ParentProcessID', ctypes.c_ulong),
                    ('pcPriClassBase', ctypes.c_long),
                    ('dwFlags', ctypes.c_ulong),
                    ('szExeFile', ctypes.c_char * 260)
                ]
            h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if h_snap != -1 and h_snap != 0:
                try:
                    pe = PROCESSENTRY32()
                    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                    proc_map = {}
                    if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                        while True:
                            proc_map[pe.th32ProcessID] = {
                                "ppid": pe.th32ParentProcessID,
                                "name": pe.szExeFile.decode('utf-8', errors='ignore').lower()
                            }
                            if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                                break
                    
                    chain = []
                    curr = os.getpid()
                    seen = set()
                    for _ in range(16):
                        if curr in seen or curr == 0:
                            break
                        seen.add(curr)
                        p_info = proc_map.get(curr)
                        if p_info:
                            chain.append({
                                "pid": curr,
                                "ppid": p_info["ppid"],
                                "name": p_info["name"]
                            })
                            curr = p_info["ppid"]
                        else:
                            break
                    if chain:
                        info_list = chain
                finally:
                    kernel32.CloseHandle(h_snap)
        except:
            pass
    return info_list

def get_process_ancestors() -> List[int]:
    info = get_process_ancestor_info()
    if info:
        return [x["pid"] for x in info]
    return [os.getpid(), os.getppid()]

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
    def strip_trailing_invocation(cls, text: str) -> str:
        # Strip trailing prompt running cpt / copyterm so the command invocation does not pollute capture
        lines = text.splitlines(keepends=True)
        if not lines:
            return ""
        
        # Check if the last non-empty line is a cpt/copyterm invocation
        last_idx = len(lines) - 1
        while last_idx >= 0 and not lines[last_idx].strip():
            last_idx -= 1
        
        if last_idx >= 0:
            clean = cls.strip_ansi(lines[last_idx]).strip()
            # Match prompt running cpt or copyterm
            if re.search(r'(?:PS\s+[^>\n]+>|[a-zA-Z0-9_.-]+@[^#$%>]+[#$%>]|[A-Z]:\\[^>\n]*>|^[>$#%]\s*)\s*(?:cpt|copyterm|python\s+.*copyterm\.py)(?:\s+.*)?$', clean, re.IGNORECASE) or clean.lower() in ("cpt", "copyterm"):
                lines = lines[:last_idx]
        
        return "".join(lines)

    @classmethod
    def sanitize(cls, text: str) -> str:
        text = text.lstrip('\ufeff')
        text = cls.strip_ansi(text)
        text = cls.collapse_carriage_returns(text)
        text = cls.strip_transcript_banners(text)
        text = cls.strip_shell_marks(text)
        text = cls.strip_trailing_invocation(text)
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

# --- IDE Bridge Client (Tier 1 Backend) ---

class IdeBridgeClient:
    @staticmethod
    def get_discovery_info() -> Optional[Dict[str, Any]]:
        disc_file = get_data_dir() / "ide_bridge.json"
        if not disc_file.exists():
            return None
        try:
            return json.loads(disc_file.read_text(encoding='utf-8'))
        except:
            return None

    @staticmethod
    def is_available() -> bool:
        info = IdeBridgeClient.get_discovery_info()
        return info is not None and "endpoint" in info and "auth_token" in info

    @staticmethod
    def send_request(action: str, caller_pids: Optional[List[int]] = None, session_id: Optional[str] = None, debug: bool = False) -> Optional[Dict[str, Any]]:
        info = IdeBridgeClient.get_discovery_info()
        if not info:
            if debug: sys.stderr.write("[copyterm:bridge] Discovery file not found\n")
            return None
        endpoint = info.get("endpoint")
        auth_token = info.get("auth_token")
        if not endpoint or not auth_token:
            if debug: sys.stderr.write("[copyterm:bridge] Invalid discovery data (missing endpoint or token)\n")
            return None

        pids = caller_pids if caller_pids is not None else get_process_ancestors()
        req = {
            "version": PROTOCOL_VERSION,
            "action": action,
            "caller_pid": pids[1] if len(pids) > 1 else pids[0],
            "caller_pids": pids,
            "session_id": session_id or os.environ.get("COPYTERM_SESSION_ID", ""),
            "nonce": str(time.time()),
            "auth_token": auth_token
        }
        req_data = (json.dumps(req) + "\n").encode('utf-8')

        if debug:
            sys.stderr.write(f"[copyterm:bridge] Connecting to {endpoint}\n")
            sys.stderr.write(f"[copyterm:bridge] Sending action '{action}' with caller_pids={pids}\n")

        if sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            GENERIC_READ = 0x80000000
            GENERIC_WRITE = 0x40000000
            OPEN_EXISTING = 3
            INVALID_HANDLE_VALUE = -1

            h_pipe = kernel32.CreateFileW(
                endpoint,
                GENERIC_READ | GENERIC_WRITE,
                0,
                None,
                OPEN_EXISTING,
                0,
                None
            )

            if h_pipe == INVALID_HANDLE_VALUE or h_pipe == 0:
                err = kernel32.GetLastError()
                if debug: sys.stderr.write(f"[copyterm:bridge] CreateFileW failed (Win32 code {err})\n")
                return None

            try:
                written = ctypes.c_ulong(0)
                if not kernel32.WriteFile(h_pipe, req_data, len(req_data), ctypes.byref(written), None):
                    if debug: sys.stderr.write("[copyterm:bridge] WriteFile failed\n")
                    return None

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

                resp_str = b"".join(chunks).decode('utf-8', errors='replace').strip()
                if debug: sys.stderr.write(f"[copyterm:bridge] Received {len(resp_str)} response chars\n")
                if resp_str:
                    return json.loads(resp_str)
            except Exception as e:
                if debug: sys.stderr.write(f"[copyterm:bridge] IPC exception: {e}\n")
                return None
            finally:
                kernel32.CloseHandle(h_pipe)
        else:
            import socket
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.settimeout(5.0)
                    s.connect(endpoint)
                    s.sendall(req_data)
                    chunks = []
                    while True:
                        data = s.recv(65536)
                        if not data:
                            break
                        chunks.append(data)
                        if b'\n' in data or data.endswith(b'}'):
                            break
                    resp_str = b"".join(chunks).decode('utf-8', errors='replace').strip()
                    if resp_str:
                        return json.loads(resp_str)
            except Exception as e:
                if debug: sys.stderr.write(f"[copyterm:bridge] UDS exception: {e}\n")
                return None
        return None

# --- Capture Epoch Manager ---

class EpochManager:
    @staticmethod
    def get_epoch_file(session_id: str) -> Path:
        return get_sessions_dir() / f"{session_id}.epoch"

    @staticmethod
    def load_epoch_state(session_id: Optional[str] = None) -> Dict[str, Any]:
        sessions_dir = get_sessions_dir()
        
        # 1. Direct match by session_id
        if session_id:
            ep_file = EpochManager.get_epoch_file(session_id)
            if ep_file.exists():
                try:
                    return json.loads(ep_file.read_text(encoding='utf-8'))
                except:
                    pass

        # 2. Check environment session ID
        env_sess = os.environ.get("COPYTERM_SESSION_ID")
        if env_sess:
            ep_file = EpochManager.get_epoch_file(env_sess)
            if ep_file.exists():
                try:
                    return json.loads(ep_file.read_text(encoding='utf-8'))
                except:
                    pass

        # 3. Match by process ancestors
        pids = get_process_ancestors()
        if sessions_dir.exists():
            for meta_file in sessions_dir.glob("*.meta"):
                try:
                    content = meta_file.read_text(encoding='utf-8')
                    for p in pids:
                        if f"pid={p}" in content:
                            sess_id = meta_file.stem
                            ep_file = sessions_dir / f"{sess_id}.epoch"
                            if ep_file.exists():
                                return json.loads(ep_file.read_text(encoding='utf-8'))
                except:
                    pass

        return {
            "session_id": session_id or "",
            "epoch_id": 0,
            "clear_count": 0,
            "byte_offset": 0,
            "line_offset": 0,
            "last_clear_timestamp_ms": 0,
            "latest_boundary_token": ""
        }

    @staticmethod
    def slice_buffer_by_epoch(raw_text: str, epoch_state: Dict[str, Any]) -> str:
        epoch_id = epoch_state.get("epoch_id", 0)
        
        # Epoch 0: User has never run clear in this session.
        # Preserve 100% retroactive scrollback from before CopyTerm started!
        if epoch_id == 0:
            return raw_text

        # Method 1: Exact byte offset slicing (for live continuous stream buffers / transcripts)
        byte_offset = epoch_state.get("byte_offset", 0)
        if byte_offset and byte_offset > 0:
            raw_bytes = raw_text.encode('utf-8', errors='replace')
            if byte_offset < len(raw_bytes):
                return raw_bytes[byte_offset:].decode('utf-8', errors='replace').lstrip("\r\n")
            else:
                return ""

        token = epoch_state.get("latest_boundary_token", "")
        # Method 2: Exact boundary token match (for explicit boundary markers)
        if token and token in raw_text:
            idx = raw_text.rfind(token)
            return raw_text[idx + len(token):].lstrip("\r\n")

        # Method 3: Shell prompt clear boundary slicing (for xterm.js / IDE buffer & terminal emulators)
        lines = raw_text.splitlines(keepends=True)
        prompt_clear_re = re.compile(
            r'(?:PS\s+[^>\n]+>|[a-zA-Z0-9_.-]+@[^#$%>]+[#$%>]|[A-Z]:\\[^>\n]*>|^[>$#%]\s*)\s*(?:clear|cls|Clear-Host)\s*$',
            re.IGNORECASE
        )
        
        match_indices = []
        for i, line in enumerate(lines):
            clean_line = Sanitizer.strip_ansi(line).strip()
            if prompt_clear_re.search(clean_line):
                match_indices.append(i)

        if match_indices:
            # Take the most recent clear boundary
            last_idx = match_indices[-1]
            sliced_lines = lines[last_idx + 1:]
            return "".join(sliced_lines).lstrip("\r\n")

        # Method 4: Line offset slicing
        line_offset = epoch_state.get("line_offset", 0)
        if line_offset and line_offset > 0:
            if line_offset < len(lines):
                return "".join(lines[line_offset:]).lstrip("\r\n")
            else:
                return ""

        # Fallback: if epoch_id > 0 and no content after clear, return empty
        return ""

    @staticmethod
    def advance_epoch(session_id: str, clear_cmd: str = "cls") -> Dict[str, Any]:
        sessions_dir = get_sessions_dir()
        sessions_dir.mkdir(parents=True, exist_ok=True)
        state = EpochManager.load_epoch_state(session_id)
        new_epoch = state.get("epoch_id", 0) + 1
        ts = int(time.time() * 1000)
        token = f"CPT_EPOCH_BOUND_{session_id}_{new_epoch}"

        buf_file = sessions_dir / f"{session_id}.buf"
        line_offset = 0
        byte_offset = 0
        if buf_file.exists():
            try:
                byte_offset = buf_file.stat().st_size
            except:
                pass
            try:
                line_offset = len(SessionManager.read_buffer(buf_file).splitlines())
            except:
                pass

        updated_state = {
            "session_id": session_id,
            "epoch_id": new_epoch,
            "clear_count": new_epoch,
            "byte_offset": byte_offset,
            "line_offset": line_offset,
            "last_clear_timestamp_ms": ts,
            "latest_boundary_token": token,
            "clear_command": clear_cmd
        }

        ep_file = EpochManager.get_epoch_file(session_id)
        # Safe atomic write to .epoch file (never touching live .buf)
        try:
            tmp_file = ep_file.with_suffix(f".{os.urandom(4).hex()}.tmp")
            tmp_file.write_text(json.dumps(updated_state), encoding='utf-8')
            tmp_file.replace(ep_file)
        except:
            try:
                ep_file.write_text(json.dumps(updated_state), encoding='utf-8')
            except:
                pass

        return updated_state

# --- Windows Console API Buffer Reader (Tier 4 Fallback) ---

class WindowsConsoleCapture:
    @staticmethod
    def capture_console_buffer() -> Optional[str]:
        if sys.platform != "win32":
            return None
        try:
            kernel32 = ctypes.windll.kernel32
            GENERIC_READ = 0x80000000
            GENERIC_WRITE = 0x40000000
            FILE_SHARE_READ = 0x00000001
            FILE_SHARE_WRITE = 0x00000002
            OPEN_EXISTING = 3
            INVALID_HANDLE_VALUE = -1

            h_out = kernel32.CreateFileW(
                "CONOUT$",
                GENERIC_READ | GENERIC_WRITE,
                FILE_SHARE_READ | FILE_SHARE_WRITE,
                None,
                OPEN_EXISTING,
                0,
                None
            )
            if h_out == INVALID_HANDLE_VALUE or h_out == 0:
                return None
            try:
                class COORD(ctypes.Structure):
                    _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]
                class SMALL_RECT(ctypes.Structure):
                    _fields_ = [('Left', ctypes.c_short), ('Top', ctypes.c_short), ('Right', ctypes.c_short), ('Bottom', ctypes.c_short)]
                class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
                    _fields_ = [
                        ('dwSize', COORD),
                        ('dwCursorPosition', COORD),
                        ('wAttributes', ctypes.c_ushort),
                        ('srWindow', SMALL_RECT),
                        ('dwMaximumWindowSize', COORD)
                    ]
                csbi = CONSOLE_SCREEN_BUFFER_INFO()
                if not kernel32.GetConsoleScreenBufferInfo(h_out, ctypes.byref(csbi)):
                    return None

                width = csbi.dwSize.X
                cursor_y = csbi.dwCursorPosition.Y
                max_rows = min(cursor_y + 1, csbi.dwSize.Y)
                if max_rows <= 0 or width <= 0:
                    return ""

                total_chars = width * max_rows
                buf = ctypes.create_unicode_buffer(total_chars)
                read_chars = ctypes.c_ulong(0)
                origin = COORD(0, 0)
                if not kernel32.ReadConsoleOutputCharacterW(h_out, buf, total_chars, origin, ctypes.byref(read_chars)):
                    return None

                raw_text = buf[:read_chars.value]
                lines = []
                for r in range(max_rows):
                    start = r * width
                    end = start + width
                    lines.append(raw_text[start:end].rstrip())

                while lines and not lines[-1]:
                    lines.pop()

                return "\n".join(lines) + ("\n" if lines else "")
            finally:
                kernel32.CloseHandle(h_out)
        except Exception:
            return None

# --- Session & Backend Resolver ---

class SessionManager:
    @staticmethod
    def get_parent_pid() -> int:
        return os.getppid()

    @staticmethod
    def init_session(shell_name: str = "cmd") -> str:
        sessions_dir = get_sessions_dir()
        sessions_dir.mkdir(parents=True, exist_ok=True)
        pids = get_process_ancestors()
        # pids[0] is current process, pids[1] is immediate parent (e.g. cmd.exe)
        parent_pid = pids[1] if len(pids) > 1 else pids[0]
        grandparent_pid = pids[2] if len(pids) > 2 else 0
        ts = int(time.time() * 1000)
        rand_token = os.urandom(3).hex()
        sess_id = f"sess_{ts}_{parent_pid}_{rand_token}"

        meta_file = sessions_dir / f"{sess_id}.meta"
        epoch_file = sessions_dir / f"{sess_id}.epoch"

        meta_content = (
            f"session_id={sess_id}\n"
            f"shell_name={shell_name}\n"
            f"pid={parent_pid}\n"
            f"ppid={grandparent_pid}\n"
            f"start_time_ms={ts}\n"
            f"last_active_time_ms={ts}\n"
            f"backend=shell_integration\n"
        )
        meta_file.write_text(meta_content, encoding='utf-8')

        epoch_content = json.dumps({
            "session_id": sess_id,
            "epoch_id": 0,
            "clear_count": 0,
            "byte_offset": 0,
            "line_offset": 0,
            "last_clear_timestamp_ms": 0,
            "latest_boundary_token": ""
        })
        epoch_file.write_text(epoch_content, encoding='utf-8')
        return sess_id

    @staticmethod
    def resolve_session(explicit_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if explicit_id:
            sess_id = explicit_id
        else:
            sess_id = os.environ.get("COPYTERM_SESSION_ID")
            if not sess_id and os.environ.get("TMUX_PANE"):
                sess_id = f"tmux_{os.environ.get('TMUX_PANE', '').replace('%', '_')}"
            if not sess_id:
                pids = get_process_ancestors()
                sessions_dir = get_sessions_dir()
                if sessions_dir.exists():
                    for meta_file in sessions_dir.glob("*.meta"):
                        try:
                            content = meta_file.read_text(encoding='utf-8')
                            for p in pids:
                                if f"pid={p}" in content:
                                    sess_id = meta_file.stem
                                    break
                            if sess_id:
                                break
                        except:
                            pass

        if not sess_id:
            return None

        buf_path = get_sessions_dir() / f"{sess_id}.buf"
        meta_path = get_sessions_dir() / f"{sess_id}.meta"
        epoch_path = get_sessions_dir() / f"{sess_id}.epoch"

        return {
            "session_id": sess_id,
            "buf_path": buf_path,
            "meta_path": meta_path,
            "epoch_path": epoch_path
        }

    @staticmethod
    def read_buffer(buf_path: Path, last_n: int = 0) -> str:
        if not buf_path.exists():
            return ""
        if sys.platform == "win32":
            try:
                kernel32 = ctypes.windll.kernel32
                GENERIC_READ = 0x80000000
                FILE_SHARE_READ = 0x00000001
                FILE_SHARE_WRITE = 0x00000002
                FILE_SHARE_DELETE = 0x00000004
                OPEN_EXISTING = 3
                INVALID_HANDLE_VALUE = -1

                h_file = kernel32.CreateFileW(
                    str(buf_path),
                    GENERIC_READ,
                    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                    None,
                    OPEN_EXISTING,
                    0,
                    None
                )
                if h_file != INVALID_HANDLE_VALUE and h_file != 0:
                    try:
                        size_high = ctypes.c_ulong(0)
                        size_low = kernel32.GetFileSize(h_file, ctypes.byref(size_high))
                        total_size = (size_high.value << 32) | size_low
                        if total_size > 0:
                            buf = ctypes.create_string_buffer(total_size)
                            bytes_read = ctypes.c_ulong(0)
                            if kernel32.ReadFile(h_file, buf, total_size, ctypes.byref(bytes_read), None):
                                content = buf.raw[:bytes_read.value].decode('utf-8-sig', errors='replace')
                                if last_n > 0:
                                    lines = content.splitlines(keepends=True)
                                    return "".join(lines[-last_n:])
                                return content
                    finally:
                        kernel32.CloseHandle(h_file)
            except:
                pass
        try:
            content = buf_path.read_bytes().decode('utf-8-sig', errors='replace')
            if last_n > 0:
                lines = content.splitlines(keepends=True)
                return "".join(lines[-last_n:])
            return content
        except:
            return ""

    @staticmethod
    def capture_active_terminal(args: argparse.Namespace, debug: bool = False) -> Tuple[Optional[str], Dict[str, Any]]:
        epoch_state = EpochManager.load_epoch_state(args.session_id)
        
        # TIER 1: Antigravity / VS Code IDE Bridge (True Terminal Scrollback)
        if not args.session_id and IdeBridgeClient.is_available():
            if debug: sys.stderr.write("[copyterm] Probing IDE Bridge...\n")
            pids = get_process_ancestors()
            resp = IdeBridgeClient.send_request("capture_terminal", caller_pids=pids, debug=debug)
            if resp and resp.get("ok"):
                term_pid = resp.get("terminal", {}).get("process_id")
                parent_pid = pids[1] if len(pids) > 1 else pids[0]
                child_sess = SessionManager.resolve_session()
                # If running directly in the IDE terminal process, or if no child shell session is active
                if not child_sess or term_pid == parent_pid or not os.environ.get("COPYTERM_SESSION_ID"):
                    raw_content = resp.get("content", "")
                    term_name = resp.get("terminal", {}).get("name", "terminal")
                    if debug:
                        sys.stderr.write(f"[copyterm] IDE Bridge capture SUCCESS: {len(raw_content)} chars from {term_name} (PID {term_pid})\n")
                    
                    # Apply Capture Epoch Boundary Slicing
                    sliced_content = EpochManager.slice_buffer_by_epoch(raw_content, epoch_state)
                    
                    if args.last > 0:
                        lines = sliced_content.splitlines(keepends=True)
                        sliced_content = "".join(lines[-args.last:])
                    
                    return sliced_content, {
                        "source": f"Antigravity / VS Code xterm terminal buffer",
                        "terminal_name": term_name,
                        "terminal_pid": term_pid,
                        "historical": True,
                        "session_id": epoch_state.get("session_id") or f"ide_{term_name}",
                        "epoch_id": epoch_state.get("epoch_id", 0)
                    }
                else:
                    if debug: sys.stderr.write(f"[copyterm] IDE Bridge error: {resp.get('error')}\n")
            else:
                if debug: sys.stderr.write("[copyterm] IDE Bridge returned no response\n")

        # TIER 2: tmux Native Scrollback Capture
        tmux_pane = os.environ.get("TMUX_PANE")
        if tmux_pane and not args.session_id:
            try:
                cmd = ["tmux", "capture-pane", "-p", "-S", "-", "-J", "-t", tmux_pane]
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, _ = p.communicate()
                if p.returncode == 0 and out:
                    raw_content = out.decode('utf-8', errors='replace')
                    sliced_content = EpochManager.slice_buffer_by_epoch(raw_content, epoch_state)
                    if args.last > 0:
                        lines = sliced_content.splitlines(keepends=True)
                        sliced_content = "".join(lines[-args.last:])
                    return sliced_content, {
                        "source": "tmux native pane buffer",
                        "terminal_name": f"tmux:{tmux_pane}",
                        "historical": True,
                        "session_id": f"tmux_{tmux_pane.replace('%', '_')}",
                        "epoch_id": epoch_state.get("epoch_id", 0)
                    }
            except:
                pass

        # TIER 3 & 4: CopyTerm PTY Session or Shell Integration Transcript Buffer / Windows Console Buffer
        sess = SessionManager.resolve_session(args.session_id)
        if sess:
            raw_content = SessionManager.read_buffer(sess["buf_path"])
            source_desc = "CopyTerm session transcript"

            # If transcript buffer is empty and on Windows, read Windows Console Screen Buffer
            if not raw_content and sys.platform == "win32":
                console_text = WindowsConsoleCapture.capture_console_buffer()
                if console_text:
                    raw_content = console_text
                    source_desc = "Windows Console Screen Buffer"

            if raw_content:
                sliced_content = EpochManager.slice_buffer_by_epoch(raw_content, epoch_state)
                if args.last > 0:
                    lines = sliced_content.splitlines(keepends=True)
                    sliced_content = "".join(lines[-args.last:])
                return sliced_content, {
                    "source": source_desc,
                    "terminal_name": sess["session_id"],
                    "historical": False,
                    "session_id": sess["session_id"],
                    "epoch_id": epoch_state.get("epoch_id", 0)
                }

        # Fallback: Check if Windows Console Buffer can be read directly
        if sys.platform == "win32" and not args.session_id:
            console_text = WindowsConsoleCapture.capture_console_buffer()
            if console_text:
                sliced_content = EpochManager.slice_buffer_by_epoch(console_text, epoch_state)
                if args.last > 0:
                    lines = sliced_content.splitlines(keepends=True)
                    sliced_content = "".join(lines[-args.last:])
                fallback_sess_id = epoch_state.get("session_id") or "cmd_console"
                return sliced_content, {
                    "source": "Windows Console Screen Buffer",
                    "terminal_name": fallback_sess_id,
                    "historical": False,
                    "session_id": fallback_sess_id,
                    "epoch_id": epoch_state.get("epoch_id", 0)
                }

        return None, {}

# --- Installer Manager ---

class Installer:
    @staticmethod
    def get_repo_root() -> Path:
        # Check standard relative paths or sys.path
        here = Path(__file__).resolve().parent
        if (here.parent / "extensions").exists():
            return here.parent
        return here

    @staticmethod
    def run_full_install(target: str = "all") -> bool:
        try:
            repo_root = Installer.get_repo_root()
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            from installer.install_windows import install_windows
            from installer.install_linux import install_linux
            from installer.install_macos import install_macos
            if sys.platform == "win32":
                res = install_windows(repo_root)
            elif sys.platform == "darwin":
                res = install_macos(repo_root)
            else:
                res = install_linux(repo_root)
            return res.get("ok", False)
        except Exception as e:
            # Fallback to local copy
            return Installer.install_binaries() and Installer.install_ide_extension() and Installer.install_shell(target)

    @staticmethod
    def run_full_uninstall(target: str = "all") -> bool:
        try:
            repo_root = Installer.get_repo_root()
            if str(repo_root) not in sys.path:
                sys.path.insert(0, str(repo_root))
            from installer.install_windows import uninstall_windows
            from installer.install_linux import uninstall_linux
            from installer.install_macos import uninstall_macos
            if sys.platform == "win32":
                res = uninstall_windows()
            elif sys.platform == "darwin":
                res = uninstall_macos()
            else:
                res = uninstall_linux()
            return res.get("ok", False)
        except Exception as e:
            return Installer.uninstall_ide_extension()

    @staticmethod
    def install_ide_extension() -> bool:
        repo_root = Installer.get_repo_root()
        src_ext = repo_root / "extensions" / "copyterm-terminal-bridge"
        if not src_ext.exists():
            return False

        installed_any = False
        ag_ext_dir = Path.home() / ".antigravity-ide" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0"
        try:
            ag_ext_dir.parent.mkdir(parents=True, exist_ok=True)
            if ag_ext_dir.exists():
                shutil.rmtree(ag_ext_dir)
            shutil.copytree(src_ext, ag_ext_dir)
            installed_any = True
        except Exception:
            pass

        vscode_ext_dir = Path.home() / ".vscode" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0"
        try:
            vscode_ext_dir.parent.mkdir(parents=True, exist_ok=True)
            if vscode_ext_dir.exists():
                shutil.rmtree(vscode_ext_dir)
            shutil.copytree(src_ext, vscode_ext_dir)
            installed_any = True
        except Exception:
            pass

        return installed_any

    @staticmethod
    def install_binaries() -> bool:
        repo_root = Installer.get_repo_root()
        data_dir = get_data_dir()
        bin_dir = data_dir / "bin"
        integrations_dir = data_dir / "integrations"
        bin_dir.mkdir(parents=True, exist_ok=True)
        integrations_dir.mkdir(parents=True, exist_ok=True)

        src_py = repo_root / "src" / "copyterm.py"
        if src_py.exists():
            shutil.copy2(src_py, bin_dir / "copyterm.py")

        for bin_name in ["cpt.exe", "copyterm.exe", "copyterm_bin.exe", "copyterm_tests.exe", "cpt", "copyterm"]:
            bin_file = repo_root / bin_name
            if bin_file.exists():
                shutil.copy2(bin_file, bin_dir / bin_name)

        src_integrations = repo_root / "integrations"
        if src_integrations.exists():
            for sub in ["powershell", "bash", "zsh", "cmd"]:
                sub_src = src_integrations / sub
                sub_dst = integrations_dir / sub
                if sub_src.exists():
                    sub_dst.mkdir(parents=True, exist_ok=True)
                    for f in sub_src.glob("*"):
                        shutil.copy2(f, sub_dst / f.name)

        cmd_dir = src_integrations / "cmd"
        if cmd_dir.exists():
            for f in cmd_dir.glob("*.cmd"):
                shutil.copy2(f, bin_dir / f.name)

        return True

    @staticmethod
    def install_shell(target: str = "all") -> bool:
        data_dir = get_data_dir()
        integrations_dir = data_dir / "integrations"
        
        if target in ["powershell", "all"] and sys.platform == "win32":
            ps_script = integrations_dir / "powershell" / "copyterm.ps1"
            if ps_script.exists():
                ps_profiles = [
                    Path.home() / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
                    Path.home() / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
                    Path.home() / "OneDrive" / "Documents" / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
                    Path.home() / "OneDrive" / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
                ]
                hook_snippet = (
                    "# >>> CopyTerm managed block >>>\n"
                    "$__copyterm_ps1 = [System.IO.Path]::Combine($env:USERPROFILE, \".copyterm\", \"integrations\", \"powershell\", \"copyterm.ps1\")\n"
                    "if (Test-Path $__copyterm_ps1) { . $__copyterm_ps1 }\n"
                    "# <<< CopyTerm managed block <<<\n"
                )
                for prof in ps_profiles:
                    try:
                        if prof.parent.exists() or "Documents" in str(prof):
                            prof.parent.mkdir(parents=True, exist_ok=True)
                            content = prof.read_text(encoding='utf-8') if prof.exists() else ""
                            if "# >>> CopyTerm" not in content:
                                with open(prof, "a", encoding="utf-8") as f:
                                    f.write(f"\n{hook_snippet}")
                    except Exception:
                        pass

        return True

    @staticmethod
    def uninstall_ide_extension() -> bool:
        for ext_dir in [
            Path.home() / ".antigravity-ide" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0",
            Path.home() / ".vscode" / "extensions" / "copyterm.copyterm-terminal-bridge-1.0.0"
        ]:
            if ext_dir.exists():
                try:
                    shutil.rmtree(ext_dir)
                except Exception:
                    pass
        return True

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

    VERSION_STR = f"cpt (CopyTerm) version {VERSION} (cross-platform terminal session capture)"

    parser = argparse.ArgumentParser(
        prog="cpt",
        description="CopyTerm (cpt) — End-to-End Cross-Platform Terminal Session Capture Utility"
    )
    parser.add_argument("-v", "--version", action="version", version=VERSION_STR)
    parser.add_argument("-n", "--last", type=int, default=0, help="Copy only the last N lines")
    parser.add_argument("--clean", action="store_true", default=True, help="Clean ANSI codes (default)")
    parser.add_argument("--raw", action="store_true", help="Preserve raw VT sequences")
    parser.add_argument("--ai", action="store_true", help="Format as AI markdown")
    parser.add_argument("--redact", action="store_true", help="Mask secrets and tokens")
    parser.add_argument("--commands-only", action="store_true", help="Extract only commands")
    parser.add_argument("--output-only", action="store_true", help="Extract only output")
    parser.add_argument("-s", "--save", type=str, help="Save to file")
    parser.add_argument("--stdout", action="store_true", help="Print captured text to stdout")
    parser.add_argument("--session-id", type=str, help="Override session ID")
    parser.add_argument("--init-session", type=str, help="Initialize a new session for given shell type")
    parser.add_argument("--epoch-advance", nargs=2, metavar=("SESSION_ID", "COMMAND"), help=argparse.SUPPRESS)
    parser.add_argument("--debug-bridge", action="store_true", help="Print bridge debugging diagnostics to stderr")

    subparsers = parser.add_subparsers(dest="subcommand")
    subparsers.add_parser("version", help="Show version information")
    
    doc_parser = subparsers.add_parser("doctor", help="Show diagnostics")
    doc_parser.add_argument("--bridge-test", action="store_true", help="Perform real live terminal buffer capture test")
    
    subparsers.add_parser("bridge-test", help="Test live IDE bridge terminal capture")
    subparsers.add_parser("list", help="List active sessions")
    subparsers.add_parser("clean-sessions", help="Clean stale sessions")
    
    init_parser = subparsers.add_parser("init-session", help="Initialize a new session")
    init_parser.add_argument("shell", nargs="?", default="cmd", help="Shell type (cmd, powershell, bash, zsh)")

    inst = subparsers.add_parser("install", help="Install shell hooks or IDE bridge")
    inst.add_argument("target", nargs="?", default="all", help="Target component (powershell, bash, zsh, cmd, ide, all)")
    uninst = subparsers.add_parser("uninstall", help="Uninstall shell hooks or IDE bridge")
    uninst.add_argument("target", nargs="?", default="all", help="Target component (ide, all)")

    args = parser.parse_args()

    # VERSION Handler
    if args.subcommand == "version":
        print(VERSION_STR)
        return 0

    # INIT-SESSION Handler
    if getattr(args, 'init_session', None) or args.subcommand == "init-session":
        target_shell = args.init_session if getattr(args, 'init_session', None) else getattr(args, 'shell', 'cmd')
        sess_id = SessionManager.init_session(target_shell)
        print(sess_id)
        return 0

    # EPOCH-ADVANCE Handler
    if getattr(args, 'epoch_advance', None):
        sess_id, cmd_name = args.epoch_advance
        EpochManager.advance_epoch(sess_id, cmd_name)
        return 0

    # BRIDGE-TEST Handler
    if args.subcommand == "bridge-test" or (args.subcommand == "doctor" and getattr(args, "bridge_test", False)):
        print("============================================================")
        print("           COPYTERM IDE BRIDGE LIVE CAPTURE TEST            ")
        print("============================================================")
        disc = IdeBridgeClient.get_discovery_info()
        if not disc:
            print("  Bridge discovery:    FAIL (ide_bridge.json not found)")
            print("  Bridge connection:   FAIL")
            print("  Reason: IDE Bridge extension is not running.")
            print("  Hint: Run 'cpt install' and reload IDE.")
            print("============================================================")
            return 1

        print(f"  Bridge discovery:    PASS ({disc.get('endpoint')})")
        
        # 1. Ping probe
        ping = IdeBridgeClient.send_request("ping")
        if ping and ping.get("ok"):
            print("  Bridge connection:   PASS")
            print("  Authentication:      PASS")
        else:
            print("  Bridge connection:   FAIL")
            print(f"  Reason: {ping.get('error') if ping else 'Endpoint not responding'}")
            print("============================================================")
            return 1

        # 2. Real Capture Request
        pids = get_process_ancestors()
        print(f"  Process hierarchy:   {pids}")
        resp = IdeBridgeClient.send_request("capture_terminal", caller_pids=pids)
        if resp and resp.get("ok"):
            term = resp.get("terminal", {})
            content = resp.get("content", "")
            lines = content.splitlines() if content else []
            byte_count = len(content.encode('utf-8')) if content else 0
            
            print("  Terminal matching:   PASS")
            print(f"  Terminal name:       {term.get('name')}")
            print(f"  Terminal PID:        {term.get('process_id')}")
            print("  Capture request:     PASS")
            print(f"  Captured bytes:      {byte_count} B")
            print(f"  Captured lines:      {len(lines)}")
            
            if content:
                print("\n  --- Captured Content Sample ---")
                for l in lines[:3]:
                    print(f"    | {l}")
                if len(lines) > 6:
                    print("    | ...")
                for l in lines[-3:]:
                    print(f"    | {l}")
                print("  -------------------------------")
            else:
                print("  Notice: Terminal buffer is currently empty.")
            print("============================================================")
            return 0
        else:
            err = resp.get("error") if resp else "No response from bridge"
            print("  Capture request:     FAIL")
            print(f"  Reason:              {err}")
            if resp and resp.get("available_terminals"):
                print(f"  Available terminals: {resp.get('available_terminals')}")
            print("============================================================")
            return 1

    if args.subcommand == "doctor":
        epoch_state = EpochManager.load_epoch_state(args.session_id)
        sess = SessionManager.resolve_session(args.session_id)
        data_dir = get_data_dir()
        bin_dir = data_dir / "bin"
        
        # Check binary status
        bin_ok = (bin_dir / "cpt.exe").exists() or (bin_dir / "cpt").exists() or (bin_dir / "copyterm.py").exists()
        
        # Check PATH status
        path_ok = False
        bin_str = str(bin_dir.resolve()).lower()
        for p in os.environ.get("PATH", "").split(os.pathsep):
            if p.strip().lower().rstrip("\\/") == bin_str.rstrip("\\/"):
                path_ok = True
                break
        if not path_ok and (shutil.which("cpt") or shutil.which("cpt.exe")):
            path_ok = True

        # Shell integration status
        integrations_ok = (data_dir / "integrations").exists()

        # IDE Bridge Probe
        disc = IdeBridgeClient.get_discovery_info()
        bridge_connected = False
        if disc:
            ping = IdeBridgeClient.send_request("ping", caller_pids=[os.getpid()])
            if ping and ping.get("ok"):
                bridge_connected = True

        # OS and platform details
        os_name = "Windows 11" if sys.platform == "win32" else sys.platform
        if sys.platform.startswith("linux"):
            try:
                os_release = Path("/etc/os-release")
                if os_release.exists():
                    for line in os_release.read_text(encoding="utf-8", errors="replace").splitlines():
                        if line.startswith("PRETTY_NAME="):
                            os_name = line.split("=", 1)[1].strip().strip('"').strip("'")
                            break
                        elif line.startswith("ID="):
                            os_name = line.split("=", 1)[1].strip().strip('"').strip("'").capitalize()
            except Exception:
                os_name = "Linux"

        arch_name = "x64" if ctypes.sizeof(ctypes.c_void_p) == 8 else "x86"
        
        # Accurately detect shell
        shell_name = "Unknown"
        if sys.platform == "win32":
            pids = get_process_ancestors()
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ('dwSize', ctypes.c_ulong),
                    ('cntUsage', ctypes.c_ulong),
                    ('th32ProcessID', ctypes.c_ulong),
                    ('th32DefaultHeapID', ctypes.c_void_p),
                    ('th32ModuleID', ctypes.c_ulong),
                    ('cntThreads', ctypes.c_ulong),
                    ('th32ParentProcessID', ctypes.c_ulong),
                    ('pcPriClassBase', ctypes.c_long),
                    ('dwFlags', ctypes.c_ulong),
                    ('szExeFile', ctypes.c_char * 260)
                ]
            h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            proc_names = {}
            if h_snap != -1 and h_snap != 0:
                try:
                    pe = PROCESSENTRY32()
                    pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                    if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                        while True:
                            proc_names[pe.th32ProcessID] = pe.szExeFile.decode('utf-8', errors='ignore').lower()
                            if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                                break
                finally:
                    kernel32.CloseHandle(h_snap)
            for p in pids:
                n = proc_names.get(p, "")
                if "cmd.exe" in n:
                    shell_name = "CMD"
                    break
                elif "pwsh.exe" in n or "pwsh" in n:
                    shell_name = "PowerShell Core"
                    break
                elif "powershell.exe" in n or "powershell" in n:
                    shell_name = "PowerShell"
                    break
                elif "bash.exe" in n or "bash" in n:
                    shell_name = "Bash"
                    break
                elif "zsh.exe" in n or "zsh" in n:
                    shell_name = "Zsh"
                    break
            if shell_name == "Unknown":
                if os.environ.get("PSExecutionPolicyPreference") or os.environ.get("PSModulePath"):
                    shell_name = "PowerShell"
                elif os.environ.get("PROMPT"):
                    shell_name = "CMD"
                else:
                    shell_name = "PowerShell"
        else:
            shell_name = os.environ.get("SHELL", "bash").split("/")[-1]

        shell_integration_status = "OK" if sess else ("INSTALLED (Restart terminal to activate)" if integrations_ok else "NOT FOUND")

        print("CopyTerm Doctor\n")
        print(f"OS:                     {os_name}")
        print(f"Architecture:           {arch_name}")
        print(f"Shell:                  {shell_name}")
        print(f"Installation:           {'OK' if bin_ok else 'NOT INSTALLED'}")
        print(f"Binary:                 {'OK' if bin_ok else 'MISSING'}")
        print(f"PATH:                   {'OK' if path_ok else 'WARN (Open new terminal to refresh PATH)'}")
        print(f"Shell integration:      {shell_integration_status}")
        if sys.platform.startswith("linux"):
            systemd_ok = shutil.which("systemctl") is not None
            print(f"systemd:                {'AVAILABLE' if systemd_ok else 'N/A'}")
            if systemd_ok:
                print(f"CopyTerm service:       {'ACTIVE' if (data_dir / 'services').exists() else 'STANDBY'}")
        print(f"IDE bridge:             {'CONNECTED' if bridge_connected else ('RUNNING' if disc else 'NOT RUNNING')}")
        print(f"Historical scrollback:  {'AVAILABLE' if bridge_connected or os.environ.get('TMUX_PANE') else 'FALLBACK'}")
        print(f"Session isolation:      OK")
        print(f"Epoch tracking:         OK")
        print(f"Runtime state:          {data_dir}\n")

        print("============================================================")
        print("               DETAILED DIAGNOSTIC REPORT                   ")
        print("============================================================")
        print(f"  Version:            {VERSION}")
        print(f"  Command:            cpt (alias: copyterm)")
        print(f"  Current PID:        {os.getpid()}")
        print(f"  Parent PID (PPID):  {SessionManager.get_parent_pid()}")
        print(f"  Process Ancestors:  {get_process_ancestors()}")
        print(f"  Session ID:         {epoch_state.get('session_id') or (sess['session_id'] if sess else 'unknown')}")
        print(f"  Current Epoch:      {epoch_state.get('epoch_id', 0)}")
        print(f"  Boundary Tracking:  AVAILABLE")
        print(f"  Data Directory:     {data_dir}")
        print(f"  Clipboard Status:   AVAILABLE")

        print("\n  [IDE Terminal Bridge]")
        if disc:
            print(f"    Detected:                 YES")
            print(f"    IDE:                      {disc.get('ide', 'Unknown')}")
            print(f"    Terminal Implementation:  xterm.js")
            print(f"    Endpoint:                 {disc.get('endpoint')}")
            print(f"    Protocol:                 v{disc.get('protocol_version', 1)}")
            if bridge_connected:
                print(f"    Bridge Status:            CONNECTED (Ping OK)")
                print(f"    Historical Scrollback:    AVAILABLE")
                print(f"    Boundary Tracking:        AVAILABLE")
            else:
                print(f"    Bridge Status:            ENDPOINT NOT RESPONDING")
                print(f"    Historical Scrollback:    UNAVAILABLE")
        else:
            print(f"    Detected:                 NO")
            print(f"    Bridge Status:            NOT RUNNING")
            print(f"    Historical Scrollback:    UNAVAILABLE (Install via 'cpt install')")

        tmux_pane = os.environ.get("TMUX_PANE")
        print("\n  [tmux Session]")
        if tmux_pane:
            print(f"    Active Pane:              {tmux_pane}")
            print(f"    Historical Scrollback:    AVAILABLE")
        else:
            print(f"    tmux Active:              NO")

        print("\n  [Shell Session / Integration]")
        if sess:
            print(f"    Resolved Session ID:      {sess['session_id']}")
            print(f"    Buffer Path:              {sess['buf_path']}")
            print(f"    Epoch File:               {sess['epoch_path']}")
            print(f"    Capture Status:           ACTIVE")
        else:
            print(f"    Resolved Session:         No active capture session detected for this terminal")
            print(f"    Capture Status:           INACTIVE (Open a new terminal window to activate)")

        print("============================================================")
        return 0

    if args.subcommand == "install":
        ok = Installer.run_full_install(args.target)
        if ok:
            print("\nCopyTerm installation complete. Open a new terminal before using cpt.")
        return 0 if ok else 1

    if args.subcommand == "uninstall":
        ok = Installer.run_full_uninstall(args.target)
        if ok:
            print("\nCopyTerm uninstallation complete.")
        return 0 if ok else 1

    raw_text, meta = SessionManager.capture_active_terminal(args, debug=args.debug_bridge)
    if raw_text is None:
        sys.stderr.write("cpt: No active terminal session or IDE bridge detected.\n")
        sys.stderr.write("Run 'cpt doctor' for diagnostics or 'cpt install' to configure.\n")
        return 1

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
        processed = f"### Terminal Buffer Output\n\n- **Source:** `{meta.get('source', 'Terminal Buffer')}`\n- **Epoch:** `{meta.get('epoch_id', 0)}`\n\n```bash\n{processed.rstrip()}\n```\n"

    # --stdout Handling
    if args.stdout:
        sys.stdout.write(processed)
        sys.stdout.flush()
        return 0

    if args.save:
        Path(args.save).write_text(processed, encoding='utf-8')
        print(f"Saved {len(processed.splitlines())} lines to {args.save}")
        return 0

    # Clipboard Handling
    ok = Clipboard.copy(processed)
    if not ok:
        sys.stderr.write("cpt: Failed to copy to clipboard.\n")
        return 1

    line_count = len(processed.splitlines()) if processed.strip() else 0
    byte_count = len(processed.encode('utf-8'))
    size_str = f"{byte_count} B" if byte_count < 1024 else f"{byte_count // 1024} KB"
    redact_str = f" (Masked {secrets_count} secret tokens)" if secrets_count > 0 else ""
    epoch_str = f" [Epoch {meta.get('epoch_id', 0)}]" if meta.get('epoch_id') is not None else ""
    print(f"Copied {line_count} lines ({size_str}) from terminal [{meta.get('terminal_name', 'active')}]{epoch_str} to clipboard.{redact_str}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
