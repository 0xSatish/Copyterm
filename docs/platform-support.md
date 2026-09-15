# COPYTERM Platform Support Matrix

This document provides a detailed breakdown of `copyterm` capabilities across operating systems, terminal emulators, shells, and multiplexers.

---

## 1. Platform Compatibility Matrix

| Operating System / Environment | Terminal Emulator | Shell | Capture Mechanism | Session Isolation | Clipboard Backend | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Windows 10 / 11** | Windows Terminal | PowerShell 5.1 | Prompt hook / PSReadLine | `$env:COPYTERM_SESSION_ID` + PPID | Win32 API | **Fully Supported** |
| **Windows 10 / 11** | Windows Terminal | PowerShell 7+ | Prompt hook / PSReadLine | `$env:COPYTERM_SESSION_ID` + PPID | Win32 API | **Fully Supported** |
| **Windows 10 / 11** | Windows Terminal | CMD (Command Prompt) | Session wrapper / Prompt macro | Process tree PPID | Win32 API | **Fully Supported** |
| **Windows 10 / 11** | Windows Console (ConHost) | PowerShell / CMD | Console Handle / Hook | Process PID | Win32 API | **Fully Supported** |
| **Ubuntu / Debian / Mint** | GNOME Terminal | Bash 4.x / 5.x | `PROMPT_COMMAND` / `trap DEBUG` | Shell PID `$$` + PTY | Wayland (`wl-copy`) / X11 (`xclip`) | **Fully Supported** |
| **Fedora / RHEL / Arch** | GNOME Terminal / Konsole | Zsh 5.x | `preexec` / `precmd` | Shell PID `$$` + PTY | Wayland (`wl-copy`) / X11 (`xclip`) | **Fully Supported** |
| **Cross-Platform** | Alacritty / Kitty / WezTerm | Bash / Zsh / Fish | Shell Integration / PTY | Shell PID `$$` + Env | Wayland / X11 / Win32 | **Fully Supported** |
| **Cross-Platform** | tmux (Multiple Panes) | Any Shell | `tmux capture-pane` | Pane ID `$TMUX_PANE` | OSC 52 / Native | **Fully Supported** |
| **Cross-Platform** | VS Code Integrated Terminal | Any Shell | Shell Integration | Shell PID + Env | Native OS Clipboard | **Fully Supported** |
| **Remote SSH** | Any Terminal | Remote Shell | Remote Hook / Session buf | Remote PID | OSC 52 Escape Sequence | **Fully Supported** |

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
