# COPYTERM Future Roadmap

This document outlines the planned evolutionary phases for `copyterm`.

---

## Phase 1 (Current Release — v1.0.0) — COMPLETED
- [x] Complete standalone single-binary C++17 core engine (`copyterm.exe` / `copyterm`).
- [x] Strict per-session isolation supporting 30+, 100+ concurrent terminals with 0% cross-contamination.
- [x] Bounded circular ring buffer (default 10 MB / 50,000 lines) with backward reverse-seek tail reader (`--last N`).
- [x] ANSI/VT escape parser with carriage return (`\r`) progress bar collapsing.
- [x] Multi-platform clipboard integration (Win32 API, Wayland `wl-copy`, X11 `xclip`/`xsel`, OSC 52).
- [x] Automated secret redaction (`--redact`) for AWS, GitHub tokens, JWTs, and private keys.
- [x] AI-ready Markdown formatting (`--ai`).
- [x] Native shell integrations for PowerShell (5.1/7+), Bash, Zsh, CMD with non-destructive, idempotent `install` / `uninstall`.
- [x] Diagnostic command (`copyterm doctor`).
- [x] Comprehensive test suite & 30-terminal concurrency isolation tests.

---

## Phase 2 (v1.1.0 — Enhancements)
- [ ] Direct Kitty IPC integration via `kitty @ get-text`.
- [ ] Direct WezTerm CLI integration via `wezterm cli get-text`.
- [ ] JSON export format (`copyterm --json`) structured with timestamped command objects.
- [ ] HTML formatted export (`copyterm --html`) with syntax highlighting for web embedding.
- [ ] Filter by command exit code (`copyterm --failed` to copy only commands that exited with non-zero status).

---

## Phase 3 (v1.2.0 — Extended Packaging & Ecosystem)
- [ ] Windows Package Manager (`winget install copyterm`) manifest.
- [ ] Homebrew tap for macOS/Linux (`brew install copyterm`).
- [ ] Arch Linux AUR package (`yay -S copyterm-bin`).
- [ ] Debian/Ubuntu `.deb` and Fedora/RHEL `.rpm` packaging workflows.

---

## Phase 4 (v2.0.0 — Opt-In AI Integration)
- [ ] Opt-in `copyterm explain` and `copyterm fix-error` CLI extensions (requiring explicit user-provided API key).
- [ ] Local Ollama integration (`copyterm --ollama`) for 100% offline terminal error analysis.
