# COPYTERM (`cpt`) Platform Support Matrix

This document provides a detailed breakdown of `cpt` capabilities across operating systems, terminal emulators, shells, and multiplexers.

---

## 1. Platform Compatibility Matrix

| Environment | Terminal Emulator | Shell | Capture Backend | Scope | Epoch Boundary Support | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Antigravity IDE** | Integrated Terminal (xterm.js 5.6) | PowerShell / Bash / Zsh | **Tier 1: IDE Bridge** | **Complete Buffer + Scrollback** | `clear`, `cls`, `Clear-Host` | **VERIFIED** |
| **VS Code** | Integrated Terminal (xterm.js) | PowerShell / Bash / Zsh | **Tier 1: IDE Bridge** | **Complete Buffer + Scrollback** | `clear`, `cls`, `Clear-Host` | **VERIFIED** |
| **tmux (Multi-Pane)** | Any Terminal / Linux / macOS | Any Shell | **Tier 2: tmux Native** | **Complete Pane Scrollback Buffer** | Shell `clear` wrapper | **VERIFIED** |
| **Standalone Windows** | Windows Terminal / ConHost | PowerShell 5.1 & 7+ | Tier 4: Shell Integration | Captured Session Stream | `Clear-Host`, `clear`, `cls` | **VERIFIED** |
| **Standalone Windows** | CMD (Command Prompt) | cmd.exe | Tier 4: Shell Integration | Captured Session Stream | `cls.cmd`, `cpt.cmd` | **VERIFIED** |
| **Standalone Linux / macOS** | GNOME Terminal / Alacritty / Kitty | Bash / Zsh | Tier 4: Shell Integration | Captured Session Stream | `clear()` shell function | **VERIFIED** |
| **Explicit PTY Session** | Any Terminal | Any Shell / REPL | Tier 3: PTY Wrapper (`cpt session`) | 100% Raw Stream from Startup | Explicit stream boundary | **VERIFIED** |

---

## 2. Platform-Specific Nuances & Details

### Antigravity IDE & VS Code Integrated Terminal
- **Capture Method:** Authenticated local IPC bridge to the xterm.js renderer.
- **Scrollback Availability:** 100% available retroactively; all retained output generated *after* `clear` is captured.
- **Line Wrapping:** Soft-wrapped lines are preserved and unwrapped without artificial `\n` characters.
- **Clipboard Guard:** Preserves and restores existing user clipboard during internal workbench serialization.

### Standalone Windows Terminal vs ConHost
- Windows Terminal does not expose a public external CLI buffer query API.
- Standalone sessions rely on the **Shell Integration** (`cpt install powershell`) or **PTY Session Wrapper** (`cpt session powershell`).
- `Clear-Host` / `clear` / `cls` flushes the prior epoch and establishes a new capture boundary.

### Linux Wayland vs X11
- **Wayland:** Automatically pipes clipboard content to `wl-copy`.
- **X11:** Uses `xclip` or `xsel`.
- **Headless / Remote Linux:** Falls back to ANSI OSC 52 clipboard sequences or `--save <file>`.

### tmux Multi-Pane Workflow
- `$TMUX` and `$TMUX_PANE` are automatically recognized.
- `cpt` issues `tmux capture-pane -p -S - -J -t <pane>` directly to the tmux server.
- Every pane in every window remains completely isolated.

### SSH Workflows
- When executed locally, `cpt` captures everything rendered in the local terminal window, including output emitted by the remote SSH host.
- When executed on a remote host, `cpt` emits ANSI OSC 52 escape sequences to copy directly to the local desktop clipboard.
