# Changelog

All notable changes to the `copyterm` project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - Initial Production Release

### Added
- **Core Engine:** Standalone, single-binary C++17 architecture with zero external runtime dependencies.
- **Strict Per-Session Isolation:** Multi-tier session resolver hierarchy guaranteeing 100% isolation across 30+ and 100+ concurrent terminals, tabs, and panes.
- **Bounded Ring Buffer:** File-backed circular ring buffer with 10 MB default limit and fast $O(\text{tail})$ backward-seek tail reader (`--last N`).
- **ANSI & VT Sanitizer:** Full ANSI/VT escape sequence stripper with a virtual 1D line buffer state machine to collapse carriage return (`\r`) progress bars and spinners.
- **Secret Redaction:** High-speed credential detection and masking (`--redact`) for AWS keys, GitHub tokens, private keys, JWTs, and passwords.
- **AI Formatting Mode:** Formatted Markdown output mode (`--ai`) with execution metadata, working directory, and code blocks.
- **Multi-Platform Clipboard Subsystem:**
  - Win32 API (`OpenClipboard`, `SetClipboardData(CF_UNICODETEXT)`) on Windows.
  - Wayland `wl-copy` and X11 `xclip` / `xsel` on Linux.
  - ANSI OSC 52 sequence generation for remote SSH sessions.
- **Shell Integrations:** Non-destructive, idempotent `install` and `uninstall` commands for PowerShell 5.1/7+, Bash, Zsh, and CMD.
- **Diagnostics:** Comprehensive `copyterm doctor` environment and session inspection tool.
- **Test Suite:** Comprehensive unit test runner (`copyterm_tests.exe`) and 30-terminal concurrency isolation integration test (`test_isolation_30_terminals.ps1`).
