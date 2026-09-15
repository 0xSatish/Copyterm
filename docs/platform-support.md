# COPYTERM Platform Support Matrix

This document provides a detailed breakdown of `copyterm` capabilities across operating systems, terminal emulators, shells, and multiplexers.

---

## 1. Platform Compatibility Matrix

| Operating System / Environment | Terminal Emulator | Shell | Capture Mechanism | Session Isolation | Clipboard Backend | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Windows 10 / 11** | Windows Terminal / ConHost | PowerShell 5.1 & 7+ | Continuous Transcript / Lifecycle Hook | `$env:COPYTERM_SESSION_ID` + PPID | Win32 API | **VERIFIED** |
| **Windows 10 / 11** | Windows Terminal / ConHost | CMD (Command Prompt) | Explicit Session Wrapper (`copyterm session`) | Process tree PPID | Win32 API | **LIMITATION (Unwrapped native CMD not captured)** |
| **Windows (Git Bash)** | Git Bash / Mintty | GNU Bash 5.x | Stream Tee / Process Substitution | Shell PID `$$` + Env | Win32 / OSC 52 | **VERIFIED** |
| **Linux (Ubuntu / Debian)** | GNOME Terminal / Alacritty | Bash 4.x / 5.x | Stream Tee / Lifecycle Hook | Shell PID `$$` + PTY | Wayland (`wl-copy`) / X11 (`xclip`) | **VERIFIED (Architecture & Bash verified)** |
| **Linux (Fedora / Arch)** | GNOME Terminal / Kitty | Zsh 5.x | `preexec` / `precmd` | Shell PID `$$` + PTY | Wayland (`wl-copy`) / X11 (`xclip`) | **Architecture Complete** |
| **Linux (WSL)** | Windows Terminal | Bash / Zsh | Shell Integration | Shell PID `$$` + Env | Wayland / Win32 | **UNTESTED (WSL not installed on host)** |
| **Cross-Platform** | tmux (Multiple Panes) | Any Shell | `tmux capture-pane` | Pane ID `$TMUX_PANE` | OSC 52 / Native | **UNTESTED on this host (tmux not installed)** |
| **Remote SSH** | Any Terminal | Remote Shell | Remote Hook / OSC 52 | Remote PID | OSC 52 Terminal Sequence | **UNTESTED (No remote host in test env)** |

---

## 2. Platform-Specific Nuances & Details

### Windows ConPTY vs Legacy ConHost
- **Modern ConPTY (Windows Terminal):** `copyterm` utilizes PowerShell / CMD lifecycle integration. The session is tagged with `$env:COPYTERM_SESSION_ID` and tracked via the Win32 Process Snapshotting engine.
- **Legacy ConHost:** If running in traditional `conhost.exe`, `copyterm` detects the active console handle and shell PID.

### Linux Wayland vs X11
- **Wayland:** Automatically pipes clipboard content to `wl-copy`.
- **X11:** Checks for `xclip` or `xsel`.
- **Headless / Remote Linux:** Falls back to ANSI OSC 52 clipboard sequences or `--save <file>` mode.

### Tmux Multi-Pane Workflow
When inside `tmux`:
- `$TMUX` and `$TMUX_PANE` are automatically recognized.
- `copyterm` issues `tmux capture-pane -p -S - -J -t <pane>` directly to tmux server.
- Every pane in every window remains completely isolated.

### SSH Workflows
- **Remote `copyterm` execution:** If installed on the remote machine, `copyterm` captures the remote session and emits OSC 52 clipboard sequences back across the SSH channel directly into your local clipboard.
- **Local `copyterm` execution:** Captures the local terminal stream up to and including the SSH session.
