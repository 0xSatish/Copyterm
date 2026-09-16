# CopyTerm

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform: Windows | Linux | macOS](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen.svg)]()
[![Python: >= 3.8](https://img.shields.io/badge/Python-%3E%3D%203.8-3776AB.svg?logo=python&logoColor=white)]()
[![C++: C++17](https://img.shields.io/badge/C%2B%2B-C%2B%2B17-00599C.svg?logo=c%2B%2B&logoColor=white)]()
[![Architecture: Capture Epoch Model](https://img.shields.io/badge/Architecture-Capture%20Epoch%20Model-orange.svg)]()

> **Copy your terminal's retained history with a single command:**
>
> ```text
> cpt
> ```

Terminal emulators retain large amounts of scrollback, but copying the entire relevant terminal history manually is slow, cumbersome, and error-prone. Selecting text across hundreds or thousands of lines with a mouse often misses lines, captures unwanted UI artifacts, or includes stale output from previous tasks.

**CopyTerm** provides a terminal-aware, directory-independent CLI utility (`cpt`, with `copyterm` as a full alias) that instantly captures your current terminal session's relevant history and places it directly onto your system clipboard.

---

## Table of Contents

- [Key Features](#key-features)
- [Why CopyTerm?](#why-copyterm)
- [How It Works](#how-it-works)
- [Installation](#installation)
  - [Windows (PowerShell)](#windows-powershell)
  - [Linux & macOS (Bash / Zsh)](#linux--macos-bash--zsh)
  - [Universal Python Installer](#universal-python-installer)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [The Capture Epoch Model (`clear` & `cls`)](#the-capture-epoch-model-clear--cls)
- [Multi-Terminal Session Isolation](#multi-terminal-session-isolation)
- [Working Directory & Repository Independence](#working-directory--repository-independence)
- [IDE Terminal Bridge](#ide-terminal-bridge)
- [Platform & Shell Support Matrix](#platform--shell-support-matrix)
- [Configuration](#configuration)
- [Diagnostics with `cpt doctor`](#diagnostics-with-cpt-doctor)
- [Security & Privacy](#security--privacy)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Technical Limitations](#technical-limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

- **⚡ Instant Single-Command Capture**: Run `cpt` from anywhere to copy your active terminal session history to your clipboard.
- **🎯 Capture Epoch Model (`clear` / `cls` Boundary)**: Running `clear` (or `cls` on Windows CMD) establishes a new capture boundary. `cpt` only captures output generated *after* the most recent clear, strictly excluding stale pre-clear history.
- **🔒 Strict Per-Terminal Isolation**: Every terminal tab, window, or pane maintains a strictly isolated session identity. Capturing in Terminal A never leaks into or reads from Terminal B.
- **🌐 CWD & Repository Independence**: Your session follows your terminal process tree, not your working directory. You can `cd` anywhere, move, or delete the source repository—`cpt` continues working seamlessly.
- **🧩 Deep IDE Integration**: Built-in IDE Bridge for Antigravity IDE and VS Code that communicates with the `xterm.js` renderer to capture true retroactive historical scrollback across thousands of lines.
- **🛡️ Automated Secret Redaction**: Built-in `--redact` flag masks API keys, AWS credentials, GitHub tokens, private keys, and JWTs before they hit the clipboard.
- **🧹 Intelligent ANSI / VT Sanitization**: Automatically strips terminal escape sequences, color codes, and cursor movement artifacts for clean, readable text.
- **🤖 AI / Markdown Formatting**: Format your terminal buffer with execution metadata ready for pasting directly into LLM prompts via `cpt --ai`.
- **🪶 Zero External Dependencies**: Implemented in clean C++17 with an autonomous zero-dependency Python core engine fallback.

---

## Why CopyTerm?

| Challenge | Traditional Approach | CopyTerm (`cpt`) |
| :--- | :--- | :--- |
| **Large Scrollback** | Manual click-and-drag scrolling | One command captures thousands of lines instantly |
| **Stale Output** | Manually trimming previous task logs | `clear` / `cls` automatically creates a capture epoch boundary |
| **Multi-Tab Workflows** | Accidental cross-terminal confusion | 100% strict per-terminal session isolation |
| **Directory Navigation** | Environment variables lost on `cd` | Complete working directory independence |
| **Sensitive Data** | Accidental clipboard leakage of API keys | Built-in high-confidence secret redactor (`--redact`) |
| **Piping & Automation** | Re-running commands with `\| clip` | Retroactive capture from existing buffer (`cpt --stdout`) |

---

## How It Works

CopyTerm operates using an intelligent **4-Tier Capture Hierarchy**, automatically selecting the highest-fidelity capture mechanism available in your current environment:

```text
┌───────────────────────────────────────────────────────────────┐
│                      cpt CLI Invocation                       │
└──────────────────────────────┬────────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   [In Antigravity / VS Code]             [In Standalone Shell]
            │                                     │
   ┌────────┴────────┐                   ┌────────┴────────┐
   ▼                 ▼                   ▼                 ▼
 Tier 1:          Tier 2:             Tier 3:           Tier 4:
IDE Bridge      tmux Session        PTY Wrapper    Shell Integration
(Full xterm.js   (Native tmux       (Full ConPTY   (Per-Session Hook
 buffer capture) capture-pane)       PTY stream)    Stream Capture)
            │                 │          │                 │
            └─────────────────┼──────────┼─────────────────┘
                              ▼
               ┌──────────────────────────────┐
               │    Epoch Boundary Filter     │
               │  (Lines since clear / cls)   │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │   Sanitizer / Redactor / AI  │
               └──────────────┬───────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  System Clipboard / stdout   │
               └──────────────────────────────┘
```

1. **Tier 1 — IDE Terminal Bridge (Highest Fidelity)**: Connects via authenticated local IPC to the CopyTerm IDE Extension in Antigravity or VS Code, extracting the full `xterm.js` viewport and retroactive scrollback lines.
2. **Tier 2 — tmux Native Capture**: When running inside a `tmux` session, queries `tmux capture-pane -p -S - -J` to capture the complete pane scrollback.
3. **Tier 3 — PTY Session Wrapper**: Wraps standalone terminal processes using ConPTY (Windows) or POSIX openpty (Linux/macOS) for byte-exact stream capture.
4. **Tier 4 — Shell Integration Hooks**: Uses lightweight, persistent shell hooks in PowerShell, CMD, Bash, and Zsh to record session streams with zero user overhead.

---

## Installation

### Windows (PowerShell)

Clone the repository and run the Windows bootstrap installer:

```powershell
git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm
.\install.ps1
```

### Linux & macOS (Bash / Zsh)

Clone the repository and execute the installation script:

```bash
git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm
chmod +x ./install.sh
./install.sh
```

### Universal Python Installer

On any platform with Python 3.8+:

```bash
git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm
python install.py
```

> [!IMPORTANT]
> **Restart Your Terminal**: After installation completes, close your current terminal window and open a **new** terminal to activate CopyTerm's automatic session capture and refreshed PATH environment.
>
> Once installed, simply type `cpt` in any terminal. You do not need to run `.\cpt.exe`, keep the repository folder, or initialize sessions manually.

---

## Quick Start

```powershell
# 1. Run your regular terminal commands
npm test
git status
docker compose ps

# 2. Copy all terminal output to clipboard
cpt

# 3. Paste anywhere (Ctrl+V / Cmd+V)
```

### Piping and File Output

```bash
# Print captured buffer directly to stdout
cpt --stdout

# Filter captured output with standard tools
cpt --stdout | grep -i "error"

# Save session buffer directly to a file
cpt --save build_log.txt
```

### Security and Formatting

```bash
# Automatically redact API keys, AWS credentials, and tokens
cpt --redact

# Format as Markdown ready for LLM / AI prompts
cpt --ai

# Copy only executed commands (stripping outputs)
cpt --commands-only

# Copy only command outputs (stripping shell prompts)
cpt --output-only
```

---

## Command Reference

The canonical short command is **`cpt`**. The legacy alias **`copyterm`** is fully supported with identical behavior.

### CLI Usage

```text
cpt [OPTIONS]
cpt <SUBCOMMAND> [OPTIONS]
```

### Subcommands

| Subcommand | Description |
| :--- | :--- |
| `cpt version` | Display canonical version information |
| `cpt doctor` | Run comprehensive environment, shell, and bridge diagnostics |
| `cpt list` | List active terminal capture sessions |
| `cpt clean-sessions` | Purge terminated and stale session buffer files |
| `cpt install [shell]` | Install shell hooks and IDE bridge integrations |
| `cpt uninstall` | Cleanly remove binaries, shell hooks, PATH entries, and extensions |

### Capture Options

| Option | Shorthand | Description |
| :--- | :--- | :--- |
| `--stdout` | | Print captured text directly to standard output |
| `-s <path>`, `--save <path>` | `-s` | Save captured output directly to the specified file path |
| `-n <N>`, `--last <N>` | `-n` | Capture only the last `N` lines of the current epoch |
| `--clean` | | Strip ANSI escape codes and normalize carriage returns (default: ON) |
| `--raw` | | Preserve exact raw ANSI / VT escape sequences |
| `--redact` | | Automatically mask sensitive API keys, tokens, and credentials |
| `--ai` | | Format output as Markdown with terminal execution metadata |
| `--commands-only` | | Extract only user-executed command lines |
| `--output-only` | | Extract only command outputs without shell prompts |
| `--session-id <id>` | | Manually target a specific session ID |
| `-v`, `--version` | `-v` | Display version information |
| `-h`, `--help` | `-h` | Display help and usage information |

---

## The Capture Epoch Model (`clear` & `cls`)

CopyTerm solves the "scrollback pollution" problem using the **Capture Epoch Model**:

```text
======================= TERMINAL BUFFER TIMELINE =======================

  [Epoch 0: Old Task]
  $ npm install
  $ gcc -O2 main.cpp -o app
  $ ./app --debug
  (300 lines of output...)

  $ clear  (or cls on CMD)  ◄── ESTABLISHES NEW CAPTURE EPOCH BOUNDARY (Epoch 1)

  [Epoch 1: Current Task]
  $ pytest -v
  $ git diff
  $ cpt                     ◄── CAPTURES ONLY EPOCH 1 (Lines after clear)

========================================================================
```

### Epoch Boundary Rules

1. **Strict Pre-Clear Exclusion**: All commands and output produced *before* the most recent `clear` (or `cls`) are strictly excluded from the clipboard.
2. **Full Post-Clear Scrollback**: If a command produces 10,000 lines of output *after* `clear`, `cpt` captures all 10,000 lines—not just the visible viewport.
3. **Echo Safety**: Commands such as `echo "clear"` or `printf "cls\n"` do **not** trigger a false epoch reset. Only genuine shell clear operations advance the boundary.
4. **Empty Post-Clear State**: Running `clear` followed immediately by `cpt` copies 0 lines (empty buffer) and never falls back to pre-clear history.
5. **Retroactive Capture Preserved**: If `clear` is never run in a session (`Epoch 0`), `cpt` captures the complete history from the beginning of the terminal buffer.

---

## Multi-Terminal Session Isolation

CopyTerm guarantees **strict per-terminal session isolation** using OS-level process ancestry tracking:

```text
Terminal Window A (PID 1024)   ──►  Session A (Epoch 2)  ──►  cpt copies Session A only
Terminal Window B (PID 2048)   ──►  Session B (Epoch 0)  ──►  cpt copies Session B only
Terminal Window C (PID 4096)   ──►  Session C (Epoch 1)  ──►  cpt copies Session C only
```

- Running `clear` in **Terminal A** only resets the boundary for Terminal A.
- Running `cpt` in **Terminal A** copies only Terminal A's output.
- Concurrently active terminals in other windows, tabs, or split panes have **0% cross-talk**.

---

## Working Directory & Repository Independence

### CWD Independence

`cpt` maintains session state independently of directory navigation:

```powershell
PS C:\> cpt                     # Works
PS C:\Users\alice\Projects> cpt # Same session, unchanged
PS C:\Users\alice\Downloads> cpt# Same session, unchanged
PS D:\Data> cpt                 # Same session, unchanged
```

- Changing directories (`cd`, `pushd`, `popd`) does not reset sessions, advance epochs, or discard scrollback.
- Session identity is anchored to your terminal process hierarchy, not the filesystem path.

### Repository Independence

Once installed via `.\install.ps1` or `install.py`, the CopyTerm runtime resides entirely in:

- **Windows**: `%USERPROFILE%\.copyterm\`
- **Linux / macOS**: `~/.copyterm/`

You can safely move, rename, or delete the cloned Git repository folder. `cpt` will continue operating autonomously from its standard user runtime path.

---

## IDE Terminal Bridge

When running inside **Antigravity IDE** or **VS Code**, CopyTerm activates its **Tier 1 IDE Terminal Bridge**:

```text
┌───────────────────────────────┐
│     Antigravity / VS Code     │
│   ┌───────────────────────┐   │
│   │ CopyTerm IDE Bridge   │   │
│   │ (xterm.js Buffer API) │   │
│   └───────────┬───────────┘   │
└───────────────┼───────────────┘
                │ Local IPC (Authenticated Pipe / Socket)
┌───────────────▼───────────────┐
│           cpt CLI             │
└───────────────────────────────┘
```

- **True Viewport + Historical Scrollback**: Directly accesses the editor's underlying `xterm.js` terminal buffer, capturing exact terminal lines including retroactive history.
- **Automatic Matching**: Discovers active terminals by querying the process tree of the calling shell.
- **Zero Configuration**: The installer automatically deploys the bridge extension to your IDE extension directory.

---

## Platform & Shell Support Matrix

| Environment / Shell | Platform | Capture Tier | Status |
| :--- | :--- | :--- | :--- |
| **PowerShell (5.1 & Core 7+)** | Windows / Linux / macOS | Tier 1 (IDE) / Tier 4 (Shell Hook) | ✅ Verified |
| **Command Prompt (CMD)** | Windows | Tier 1 (IDE) / Tier 4 (Console API / PATH Wrapper) | ✅ Verified |
| **Antigravity IDE** | Windows / Linux / macOS | Tier 1 (IDE Terminal Bridge) | ✅ Verified |
| **VS Code** | Windows / Linux / macOS | Tier 1 (IDE Terminal Bridge) | ✅ Verified |
| **Bash** | Linux / macOS / WSL | Tier 1 (IDE) / Tier 4 (PROMPT_COMMAND) | ✅ Implemented |
| **Zsh** | Linux / macOS | Tier 1 (IDE) / Tier 4 (precmd Hook) | ✅ Implemented |
| **tmux** | Linux / macOS / WSL | Tier 2 (tmux capture-pane) | ✅ Implemented |
| **SSH Sessions** | Remote Hosts | Tier 4 (Shell Hook) / Tier 3 (PTY) | ⚠️ Env-dependent |

---

## Configuration

CopyTerm stores its configuration in `~/.copyterm/config.json` (`%USERPROFILE%\.copyterm\config.json` on Windows):

```json
{
  "version": "1.1.0",
  "default_clean": true,
  "capture_tier_order": [
    "ide_bridge",
    "tmux",
    "transcript"
  ],
  "max_history_lines": 50000,
  "redaction": {
    "mask_aws_keys": true,
    "mask_github_tokens": true,
    "mask_jwt": true,
    "mask_private_keys": true
  }
}
```

---

## Diagnostics with `cpt doctor`

Run `cpt doctor` at any time to inspect your terminal environment, session resolution, and bridge connectivity:

```text
CopyTerm Doctor

OS:                     Windows 11
Architecture:           x64
Shell:                  PowerShell
Installation:           OK
Binary:                 OK
PATH:                   OK
Shell integration:      OK
IDE bridge:             CONNECTED
Historical scrollback:  AVAILABLE
Session isolation:      OK
Epoch tracking:         OK
Runtime state:          C:\Users\<user>\.copyterm

============================================================
               DETAILED DIAGNOSTIC REPORT                   
============================================================
  Version:            1.1.0
  Command:            cpt (alias: copyterm)
  Current PID:        18240
  Parent PID (PPID):  24892
  Session ID:         sess_1789540504434_24892_b26fee
  Current Epoch:      0
  Boundary Tracking:  AVAILABLE
  Data Directory:     C:\Users\<user>\.copyterm
  Clipboard Status:   AVAILABLE

  [IDE Terminal Bridge]
    Detected:                 YES
    IDE:                      Antigravity
    Terminal Implementation:  xterm.js
    Endpoint:                 \\.\pipe\copyterm-ide-fbcd21f1
    Protocol:                 v1
    Bridge Status:            CONNECTED (Ping OK)
    Historical Scrollback:    AVAILABLE
    Boundary Tracking:        AVAILABLE
============================================================
```

---

## Security & Privacy

- **Process Ancestry Verification**: Callers are authenticated against the OS process hierarchy to prevent unauthorized session snooping across different users or processes.
- **Local-Only IPC**: The IDE Bridge communicates exclusively over local named pipes (`\\.\pipe\copyterm-ide-*` on Windows) or UNIX domain sockets (`/tmp/copyterm-ide-*.sock` on POSIX) with per-instance random tokens.
- **Automated Credential Redaction**: The `--redact` flag uses high-confidence regex patterns to mask sensitive tokens:
  - AWS Access Key IDs (`AKIA...`)
  - GitHub Personal Access Tokens (`ghp_...`, `gho_...`)
  - JSON Web Tokens (`eyJ...`)
  - RSA / OpenSSH Private Keys (`-----BEGIN RSA PRIVATE KEY-----`)
  - Generic passwords and secret bearer tokens
- **Sanitized Logging**: Diagnostic logs never output raw terminal buffer content.

---

## Troubleshooting

### `cpt` is not recognized as a command

1. Close your current terminal window and open a **new** terminal window (environment PATH changes take effect in new processes).
2. Verify that `%USERPROFILE%\.copyterm\bin` (Windows) or `~/.copyterm/bin` (POSIX) exists and is present in your PATH.
3. Run `python install.py` to re-register PATH if necessary.

### "No active capture session detected for this terminal"

1. Run `cpt doctor` to see diagnostic information about your shell integration.
2. Ensure you have restarted your terminal after running `copyterm install` or `.\install.ps1`.
3. In CMD, run `cpt` or `copyterm` directly from PATH (%USERPROFILE%\.copyterm\bin).

### IDE Bridge not responding

1. Verify that the CopyTerm extension is enabled in Antigravity / VS Code.
2. Reload your IDE window (`Ctrl+Shift+P` -> `Developer: Reload Window`).
3. Run `cpt doctor --bridge-test` to test the live bridge endpoint.

---

## Project Structure

```text
Copyterm/
├── src/                        # Core C++ and Python engines
│   ├── cli/                    # CLI parsing and command dispatch
│   ├── core/                   # Session manager, ring buffer, redactor, sanitizer
│   ├── installer/              # C++ installer module
│   ├── platform/               # OS abstraction (process ancestry, clipboard, env)
│   └── copyterm.py             # Python zero-dependency engine
├── installer/                  # Cross-platform Python installer package
│   ├── configure_path.py       # Idempotent PATH management
│   ├── configure_shell.py      # Profile hooks (PowerShell, Bash, Zsh)
│   ├── install_windows.py      # Windows installation backend
│   ├── install_linux.py        # Linux installation backend
│   └── install_macos.py        # macOS installation backend
├── integrations/               # Shell hooks & wrappers
│   ├── powershell/             # PowerShell integration (copyterm.ps1)
│   ├── cmd/                    # CMD integration (cpt.cmd, copyterm_init.cmd, cls.cmd)
│   ├── bash/                   # Bash integration (copyterm.bash)
│   └── zsh/                    # Zsh integration (copyterm.zsh)
├── extensions/                 # IDE Bridge extensions
│   ├── copyterm-terminal-bridge/ # VS Code / Antigravity terminal bridge
│   └── antigravity-terminal-poc/ # POC extension
├── scripts/                    # Build scripts & non-interactive verification suites
│   ├── build.ps1               # C++ build script (Windows)
│   └── build.sh                # C++ build script (POSIX)
├── tests/                      # Unit test suites (C++ / GoogleTest / standalone)
├── docs/                       # Architectural specs, security models & guides
├── install.ps1                 # Windows one-click installer
├── install.py                  # Universal cross-platform installer
├── install.sh                  # Linux / macOS installer
├── uninstall.ps1               # Windows uninstaller
├── uninstall.sh                # Linux / macOS uninstaller
├── README.md                   # Project documentation
├── CHANGELOG.md                # Release changelog
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # MIT License
└── .gitignore                  # Git ignore rules
```

---

## Technical Limitations

- **Standalone Legacy Consoles**: In pure legacy Windows Console (`conhost.exe`) without IDE Bridge or PTY wrapper, retroactive capture prior to shell integration startup relies on transcript recording.
- **SSH Sessions**: Session capture on remote SSH hosts requires CopyTerm to be installed on the remote host, or running inside a remote `tmux` session.

---

## Roadmap

- [x] Canonical short CLI `cpt` with full backward-compatible `copyterm` alias
- [x] Capture Epoch Model (`clear` and `cls` boundary isolation)
- [x] Multi-terminal process ancestry matching and strict session isolation
- [x] CWD and repository independence
- [x] Antigravity IDE and VS Code Terminal Bridge extension
- [x] PowerShell, CMD, Bash, and Zsh shell integrations
- [x] High-confidence automated secret redaction (`--redact`)
- [ ] Windows Terminal (wt.exe) native tab bridge extension
- [ ] Direct export to GitHub Gist / pastebins (`cpt --gist`)
- [ ] Native macOS iTerm2 / Terminal.app AppleScript bridge

---

## Contributing

Contributions are welcome! Please review [CONTRIBUTING.md](CONTRIBUTING.md) for details on code style, testing guidelines, and architectural principles before submitting a pull request.

---

## License

This project is licensed under the [MIT License](LICENSE). Copyright (c) 2026.
