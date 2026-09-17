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

Terminal emulators can keep hundreds or thousands of lines in their scrollback. Copying all of that text manually is slow and easy to get wrong.

**CopyTerm** is a terminal capture utility with a simple command:

```text
cpt
```

It captures the relevant content from the current terminal session and copies it to the system clipboard. The command works independently of the current working directory.

The full command name is also available:

```text
copyterm
```

---

## Table of Contents

- [Key Features](#key-features)
- [Why CopyTerm?](#why-copyterm)
- [How It Works](#how-it-works)
- [Installation](#installation)
  - [Windows (PowerShell)](#windows-powershell)
  - [Linux and macOS (Bash / Zsh)](#linux-and-macos-bash--zsh)
  - [Universal Python Installer](#universal-python-installer)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Capture Sources](#capture-sources)
- [The Capture Epoch Model (`clear` and `cls`)](#the-capture-epoch-model-clear-and-cls)
- [Terminal Isolation](#terminal-isolation)
- [Antigravity and VS Code](#antigravity-and-vs-code)
- [Security and Privacy](#security-and-privacy)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Project Structure](#project-structure)
- [License](#license)

---

## Key Features

- Capture terminal history with one command.
- Copy the result directly to the system clipboard.
- Print the captured content with `cpt --stdout`.
- Save captured content to a file with `cpt --save`.
- Capture retained terminal scrollback when a supported IDE bridge is available.
- Support PowerShell, CMD, Bash, Zsh, SSH sessions, and tmux where supported.
- Keep terminal sessions isolated from each other.
- Treat `clear` and `cls` as capture boundaries.
- Work from any current working directory.
- Provide diagnostics with `cpt doctor`.
- Support `cpt` as the short command and `copyterm` as the full alias.
- Keep runtime session data outside the project directory.

---

## Why CopyTerm?

Normally, copying a long terminal session means selecting text with the mouse and scrolling through the terminal.

That causes several common problems:

- Some lines can be missed.
- Too much unrelated text can be selected.
- Large terminal histories take time to copy.
- Terminal output can contain formatting characters that are difficult to select cleanly.
- Old output can accidentally be included after starting a new task.

CopyTerm handles the capture from the terminal session instead of requiring manual selection.

For supported IDE terminals, CopyTerm can access the terminal emulator's retained scrollback through its IDE bridge. For normal shell sessions, it uses the available shell integration or terminal capture method.

---

## How It Works

CopyTerm uses several capture methods. It selects the most suitable method available in the current environment.

The general order is:

```text
1. IDE terminal bridge
        |
        v
2. tmux pane buffer
        |
        v
3. Shell session buffer
        |
        v
4. Windows console buffer or other platform fallback
```

The exact source depends on the terminal and shell being used.

### IDE terminal bridge

Antigravity and supported VS Code based terminals use xterm.js for their integrated terminal.

A CopyTerm bridge can request the retained terminal buffer directly from the IDE. This allows CopyTerm to capture terminal history that a normal child process cannot access.

This is especially useful when the required output is already above the visible terminal area.

### tmux

When CopyTerm is running inside tmux, it can use the tmux pane buffer to obtain retained terminal content.

### Shell session buffer

For shells such as PowerShell, CopyTerm maintains a session-specific capture buffer.

The buffer belongs to the current terminal session. It is not a single global file shared by every terminal.

### Platform fallback

If a higher-level capture source is not available, CopyTerm can use platform-specific terminal buffer support where available.

No capture method should silently use an unrelated terminal session.

---

## Installation

CopyTerm keeps its runtime state outside the repository.

On Windows, the default runtime directory is:

```text
%USERPROFILE%\.copyterm
```

On Linux and macOS:

```text
~/.copyterm
```

The project directory is used for installation and development. Runtime session files are stored separately.

### Windows (PowerShell)

Requirements:

- Windows 10 or newer
- PowerShell 5.1 or newer
- Python 3.8 or newer

Clone the repository:

```powershell
git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm
```

Run the installer:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install.ps1
```

The installer configures the required files, PATH entries, shell integration, runtime directory, and supported IDE bridge components.

After installation, close the current terminal and open a new PowerShell terminal.

Verify:

```powershell
cpt version
cpt doctor
```

You can also check command resolution:

```powershell
Get-Command cpt
Get-Command copyterm
```

The installer does not use CMD AutoRun. This is intentional. It avoids recursive `cmd.exe` startup and unnecessary background processes.

### Linux and macOS (Bash / Zsh)

Requirements:

- Python 3.8 or newer
- Bash or Zsh
- Standard Unix utilities

Clone the repository:

```bash
git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm
```

Run:

```bash
chmod +x install.sh
./install.sh
```

Open a new terminal after installation.

Verify:

```bash
cpt version
cpt doctor
```

### Universal Python Installer

The Python installer can be used when you want to run the installation through Python:

```bash
python install.py
```

If your system uses `python3`:

```bash
python3 install.py
```

After installation, open a new terminal and run:

```bash
cpt doctor
```

---

## Quick Start

Run:

```text
cpt
```

CopyTerm captures the current terminal session and copies the processed result to the clipboard.

Example:

```text
PS C:\project> python build.py
Build completed successfully.

PS C:\project> cpt
Copied 18 lines (2 KB) from terminal [powershell] [Epoch 0] to clipboard.
```

Paste the clipboard contents into your editor, issue tracker, chat, documentation, or other application.

### Print instead of copying

Use:

```text
cpt --stdout
```

This prints the captured content to standard output and does not intentionally change the clipboard.

This is useful for scripts and debugging.

### Save to a file

Use:

```text
cpt --save capture.txt
```

### Capture only the last N lines

Use:

```text
cpt --last 50
```

or:

```text
cpt -n 50
```

### Use the full command name

The following is equivalent to `cpt`:

```text
copyterm
```

For example:

```text
copyterm --stdout
```

---

## Command Reference

### Capture options

| Command | Description |
|---|---|
| `cpt` | Capture the current terminal and copy it to the clipboard |
| `cpt --stdout` | Print the processed capture to stdout |
| `cpt --save FILE` | Save the processed capture to a file |
| `cpt --last N` | Capture only the last N lines |
| `cpt -n N` | Short form of `--last` |
| `cpt --clean` | Remove terminal formatting from the capture |
| `cpt --raw` | Preserve raw terminal escape sequences |
| `cpt --commands-only` | Return detected commands |
| `cpt --output-only` | Return detected command output |
| `cpt --redact` | Mask detected secrets and tokens |
| `cpt --ai` | Format the capture as AI-friendly Markdown |
| `cpt --session-id ID` | Explicitly select a CopyTerm session |
| `cpt --debug-bridge` | Print safe IDE bridge diagnostics to stderr |

### Management commands

| Command | Description |
|---|---|
| `cpt version` | Show the CopyTerm version |
| `cpt doctor` | Show installation and session diagnostics |
| `cpt bridge-test` | Test the live IDE bridge |
| `cpt list` | List active CopyTerm sessions |
| `cpt clean-sessions` | Clean stale session data |
| `cpt install` | Configure CopyTerm integration |
| `cpt uninstall` | Remove CopyTerm integration |

### Version commands

These should report the same CopyTerm version:

```text
cpt version
cpt --version
cpt -v
copyterm version
```

---

## Capture Sources

CopyTerm does not assume that every terminal provides the same level of access.

### Antigravity and VS Code terminals

The IDE bridge can access the terminal emulator's retained scrollback.

This is the preferred method when the bridge is available.

### tmux

CopyTerm can use the active tmux pane buffer.

### Shell integration

Shell integration records terminal session data for supported shells.

This provides a reliable shell-level capture even when the terminal emulator does not expose its scrollback to child processes.

### Windows console fallback

On supported Windows console environments, CopyTerm can attempt to read the Windows console screen buffer.

The available history depends on the console environment and its configured scrollback.

---

## The Capture Epoch Model (`clear` and `cls`)

CopyTerm treats `clear` and `cls` as capture boundaries.

This does not mean CopyTerm destroys the terminal emulator's scrollback.

Instead, CopyTerm records where the new capture period starts.

### Example

Before clearing:

```text
BUILD_STARTED
BUILD_WARNING
OLD_OUTPUT
```

Run:

```text
clear
```

Then:

```text
BUILD_FINISHED
NEW_OUTPUT
```

Running:

```text
cpt --stdout
```

should return the content from the current epoch:

```text
BUILD_FINISHED
NEW_OUTPUT
```

The older content is excluded.

### Multiple clears

The most recent clear is the active boundary.

For example:

```text
FIRST_EPOCH
clear
SECOND_EPOCH
clear
THIRD_EPOCH
```

The next capture belongs to the third epoch.

### Empty epoch

If you run:

```text
clear
```

and immediately run:

```text
cpt --stdout
```

CopyTerm must not fall back to content from before the clear.

The result should be empty if no content exists in the new epoch.

### Text containing `clear`

CopyTerm does not treat ordinary output containing the word `clear` as a boundary.

For example:

```text
echo "clear"
```

does not advance the capture epoch.

The same applies to normal output such as:

```text
this output contains the word clear
```

Only the configured shell clear operation should create a boundary.

### PowerShell file locking

PowerShell transcripts can keep the active session buffer open.

CopyTerm therefore records the clear boundary without trying to write a marker into the actively locked buffer file.

This avoids file-sharing conflicts during `clear` or `Clear-Host`.

---

## Terminal Isolation

Each terminal session gets its own CopyTerm session.

For example:

```text
Terminal A
    |
    +-- session_A.buf

Terminal B
    |
    +-- session_B.buf

Terminal C
    |
    +-- session_C.buf
```

Running:

```text
cpt
```

in Terminal A should capture Terminal A's session.

It must not capture the newest buffer belonging to Terminal B or Terminal C.

CopyTerm uses session identifiers and process relationships where appropriate to associate the command with the correct terminal.

An explicit session can be selected with:

```text
cpt --session-id SESSION_ID
```

The session ID is mainly useful for diagnostics and testing.

---

## Antigravity and VS Code

CopyTerm includes an IDE terminal bridge for supported Antigravity and VS Code based environments.

The bridge allows CopyTerm to request the terminal emulator's retained xterm.js buffer.

This is important because a normal child process cannot generally read the terminal emulator's historical scrollback after it has been rendered.

### Check bridge status

Inside the IDE terminal:

```text
cpt doctor
```

A working bridge should report information similar to:

```text
[IDE Terminal Bridge]
    Detected: YES
    Bridge Status: CONNECTED
    Historical Scrollback: AVAILABLE
```

You can run a live bridge test:

```text
cpt bridge-test
```

### If the bridge is not available

The terminal can still use another supported capture method.

For example:

```text
[IDE Terminal Bridge]
    Detected: NO
```

does not necessarily mean CopyTerm itself is broken. It means the IDE bridge is not currently available.

Check the installation and restart the IDE after installing or updating the bridge.

---

## Security and Privacy

CopyTerm processes terminal content because terminal capture is its main purpose.

For this reason:

- Do not run `cpt` in a terminal containing information you do not want copied.
- Use `--redact` when working with output that may contain secrets.
- CopyTerm should not write terminal contents to diagnostic logs.
- Bridge authentication data should remain in CopyTerm's runtime directory.
- Runtime session data is stored under `~/.copyterm` or `%USERPROFILE%\.copyterm`.
- Runtime files should not be committed to Git.

`--debug-bridge` is intended for diagnostics. It should report connection and session metadata without printing terminal contents or authentication tokens.

---

## Troubleshooting

### `cpt` is not recognized

Open a new terminal after installation.

On Windows, check:

```powershell
Get-Command cpt
Get-Command copyterm
```

Also run:

```powershell
cpt doctor
```

If PATH was changed during installation, the existing terminal may not have the updated PATH.

### `cpt` works but capture is empty

Run:

```text
cpt doctor
```

Check:

- the resolved session ID
- capture status
- buffer path
- epoch
- IDE bridge status

Then run:

```text
cpt --stdout
```

If you are using Antigravity or VS Code, also run:

```text
cpt bridge-test
```

### `cpt --stdout` prints nothing

Check the active session first:

```text
cpt doctor
```

Then verify that the terminal has produced output after the session was initialized.

For debugging:

```text
cpt --debug-bridge --stdout
```

Debug information should go to stderr, while captured terminal content goes to stdout.

### `clear` or `cls` gives old output

Check the current epoch:

```text
cpt doctor
```

The capture should use the latest epoch boundary.

CopyTerm must not fall back to an older epoch when the current epoch is empty.

### PowerShell reports a file-sharing or file-locking error

Do not manually delete an active `.buf` file.

Close the affected terminal and open a new one.

If the problem continues:

```powershell
cpt doctor
```

Check whether another CopyTerm or IDE process is still using the session.

### Too many `cmd.exe` processes appear

CopyTerm does not intentionally use CMD AutoRun.

Check that no old CopyTerm AutoRun entry exists:

```powershell
Get-ItemProperty `
    "HKCU:\Software\Microsoft\Command Processor" `
    -ErrorAction SilentlyContinue
```

CopyTerm should not install a recursive CMD startup hook.

If an older installation created an AutoRun entry, remove only the CopyTerm-specific entry after confirming what it contains.

### IDE bridge is not connected

Run:

```text
cpt doctor
```

Then:

```text
cpt bridge-test
```

Restart the IDE after installing or updating the bridge.

The bridge only works while the supported IDE extension is running.

---

## Development

Clone the repository:

```bash
git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm
```

The Python core requires Python 3.8 or newer.

Run the CLI directly:

```bash
python src/copyterm.py --help
```

Check the version:

```bash
python src/copyterm.py version
```

Run the test suite using the test commands documented by the project.

Before committing changes, check:

```bash
git status
git diff
git diff --check
```

Do not commit runtime state such as:

```text
*.buf
*.epoch
```

or local CopyTerm runtime directories.

### Installer development

Validate the Windows installer before committing:

```powershell
$errors = $null

[void][System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path .\install.ps1),
    [ref]$null,
    [ref]$errors
)

$errors
```

The command should return no parser errors.

Test the installer from a fresh checkout when changing installation logic.

---

## Project Structure

A simplified project layout is:

```text
Copyterm/
|
+-- src/
|   +-- copyterm.py
|   +-- cli/
|   +-- core/
|   +-- installer/
|
+-- integrations/
|   +-- powershell/
|   +-- bash/
|   +-- zsh/
|   +-- cmd/
|
+-- extensions/
|   +-- copyterm-terminal-bridge/
|
+-- installer/
|
+-- tests/
|
+-- scripts/
|
+-- docs/
|
+-- install.ps1
+-- install.sh
+-- install.py
+-- uninstall.ps1
+-- uninstall.sh
+-- README.md
+-- CHANGELOG.md
+-- LICENSE
```

Runtime data is stored separately:

```text
Windows:
    %USERPROFILE%\.copyterm

Linux/macOS:
    ~/.copyterm
```

This separation allows CopyTerm to work from any project directory and keeps runtime data out of the source tree.

---

## Design Principles

CopyTerm follows a few simple rules:

1. Capture the current terminal, not an unrelated terminal.
2. Keep terminal sessions isolated.
3. Preserve historical scrollback when the environment provides access to it.
4. Treat `clear` and `cls` as capture boundaries.
5. Do not use dangerous recursive shell startup hooks.
6. Keep runtime state outside the repository.
7. Keep `--stdout` suitable for scripts and pipelines.
8. Do not expose terminal contents or secrets through diagnostics.
9. Prefer the terminal emulator's own buffer when a supported IDE bridge is available.
10. Fail clearly instead of silently returning data from the wrong session.

---

## Known Limitations

Terminal capabilities differ between operating systems and terminal emulators.

In particular:

- A normal child process cannot generally access an emulator's complete historical scrollback.
- Historical scrollback capture depends on the terminal or IDE exposing that information.
- Windows console buffer access depends on the console environment.
- Shell transcripts capture shell-level activity and are not identical to emulator scrollback.
- Some terminal applications may provide limited or no access to historical content.
- The amount of retained history is controlled partly by the terminal emulator itself.

CopyTerm chooses the best available capture source and should never use an unrelated session as a fallback.

---

## License

CopyTerm is released under the MIT License.

See [LICENSE](LICENSE) for the full license text.
