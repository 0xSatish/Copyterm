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

Copying a large amount of terminal output manually can be annoying. You have to select the text, scroll through the terminal, and make sure you did not miss anything.

**CopyTerm** is a small command line tool that lets you capture terminal content and copy it to your system clipboard.

The main command is `cpt`. The `copyterm` command is also supported as an alias.

It is designed to work with normal terminals, shell integrations, terminal multiplexers, and supported IDE terminals.

---

## Table of Contents

- [Key Features](#key-features)
- [Why CopyTerm](#why-copyterm)
- [How It Works](#how-it-works)
- [Supported Environments](#supported-environments)
- [Installation](#installation)
  - [Windows PowerShell](#windows-powershell)
  - [Linux and macOS](#linux-and-macos)
  - [Universal Python Installer](#universal-python-installer)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Capture Modes](#capture-modes)
- [The Capture Epoch Model](#the-capture-epoch-model)
- [Terminal Isolation](#terminal-isolation)
- [IDE Terminal Bridge](#ide-terminal-bridge)
- [Configuration and Runtime Files](#configuration-and-runtime-files)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Security](#security)
- [Project Structure](#project-structure)
- [License](#license)

---

## Key Features

- Capture terminal history with `cpt`
- Copy the captured content directly to the clipboard
- Print the captured content with `cpt --stdout`
- Save terminal content to a file
- Capture only the last N lines
- Capture commands only
- Capture output only
- Remove ANSI terminal escape sequences by default
- Optional raw terminal output
- Optional secret and token redaction
- Per-terminal session isolation
- Capture epoch support for `clear` and `cls`
- Historical scrollback support through the IDE bridge
- tmux pane capture support
- Works independently of the current working directory
- Windows, Linux, and macOS support
- No external Python packages required by the core engine

---

## Why CopyTerm

A terminal can contain much more information than what is currently visible.

For example:

```text
$ make
...
hundreds of lines of compiler output
...
$ ./app
...
application output
...

Normally, you have to manually select the text and copy it.

With CopyTerm:

$ cpt
Copied 250 lines from terminal to clipboard.

You can then paste the captured content into:

ChatGPT

Claude

GitHub issues

Documentation

Text editors

Log files

Bug reports

Remote support messages


The goal is simple: make terminal history easy to capture without manually selecting it.


---

How It Works

CopyTerm uses different capture methods depending on the environment.

The general capture order is:

Current Terminal
      |
      v
IDE Terminal Bridge
      |
      v
tmux
      |
      v
Shell Integration / Session Buffer
      |
      v
Platform Console Capture

The first usable source is used.

IDE terminals

Supported IDE terminals can expose their terminal buffer through the CopyTerm bridge.

This allows CopyTerm to access historical terminal content that a normal child process cannot access directly.

tmux

When CopyTerm is running inside tmux, it can use the tmux pane buffer to obtain retained terminal content.

Shell integration

On supported shells, CopyTerm keeps a session-specific buffer containing terminal activity.

This is useful when direct terminal emulator scrollback is not available.

Platform fallback

On Windows, CopyTerm can also try to read the Windows console screen buffer when the other capture methods are unavailable.


---

Supported Environments

CopyTerm is designed for:

Environment	Support

Windows PowerShell	Yes
Windows CMD	Yes
Windows Terminal	Depends on terminal integration
Windows Console	Yes
Linux Bash	Yes
Linux Zsh	Yes
macOS Bash	Yes
macOS Zsh	Yes
SSH sessions	Shell integration dependent
tmux	Yes
VS Code terminal	Supported through IDE bridge
Antigravity terminal	Supported through IDE bridge


Terminal emulator behavior differs between platforms. In particular, a normal child process cannot always access the emulator's historical scrollback. When an IDE bridge is available, CopyTerm uses that bridge instead.


---

Installation

Windows PowerShell

Clone the repository:

git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm

Run the installer:

powershell -ExecutionPolicy Bypass -File .\install.ps1

After installation, open a new PowerShell terminal.

Check the installation:

cpt version

Run diagnostics:

cpt doctor

Check that the commands are available:

Get-Command cpt
Get-Command copyterm

The installer stores runtime data under:

%USERPROFILE%\.copyterm

The repository itself is not used to store active terminal session data.

Important Windows note

CopyTerm does not use CMD AutoRun.

This is intentional. Automatically starting shell processes through CMD AutoRun can cause recursive cmd.exe processes and unnecessary memory usage.

CopyTerm uses direct command and PATH based integration instead.


---

Linux and macOS

Clone the repository:

git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm

Run:

chmod +x install.sh
./install.sh

Open a new terminal after installation.

Check:

cpt version

Then:

cpt doctor


---

Universal Python Installer

Python 3.8 or newer is required.

From the repository:

python install.py

On Windows:

python .\install.py

On Linux or macOS:

python3 install.py

After installation, open a new terminal and run:

cpt version


---

Quick Start

Copy terminal history

Run:

cpt

Example:

Copied 128 lines (5 KB) from terminal [active] [Epoch 0] to clipboard.

The captured content is now available in the system clipboard.


---

Print terminal history

Use:

cpt --stdout

This prints the captured content to stdout.

It does not intentionally modify the clipboard.

Example:

cpt --stdout

You can also redirect it:

cpt --stdout > terminal.txt


---

Save terminal history

cpt --save terminal.txt

The captured content is written to the specified file.


---

Copy only the last N lines

cpt --last 50

or:

cpt -n 50


---

Use the full command name

copyterm is supported as an alias:

copyterm

For example:

copyterm --stdout


---

Command Reference

Basic commands

cpt

Capture the current terminal content and copy it to the clipboard.

cpt

copyterm

Full command name for cpt.

copyterm


---

Version

cpt version

Also supported:

cpt --version
cpt -v
copyterm version


---

Diagnostics

cpt doctor

Shows information about:

CopyTerm version

Operating system

Architecture

Shell

Installation

PATH

Active session

Buffer path

Epoch state

IDE bridge

tmux

Capture status



---

IDE bridge test

cpt bridge-test

This tests communication with the supported IDE terminal bridge.

You can also run:

cpt doctor --bridge-test


---

List sessions

cpt list

Lists CopyTerm sessions known to the current runtime.


---

Clean old sessions

cpt clean-sessions

Use this to remove stale CopyTerm session data.


---

Last N lines

cpt --last 100

or:

cpt -n 100


---

Standard output

cpt --stdout

This is useful when CopyTerm is used in scripts or pipelines.

Example:

cpt --stdout > terminal-output.txt


---

Save to a file

cpt --save output.txt


---

Raw output

By default, CopyTerm cleans common terminal formatting sequences.

To preserve raw terminal sequences:

cpt --raw


---

Clean output

Cleaning is enabled by default:

cpt --clean

This removes common ANSI and terminal control sequences from the captured text.


---

Redact secrets

Use:

cpt --redact

This attempts to mask common secrets and token patterns before the content is copied or saved.

Redaction is pattern based and should not be treated as a guarantee that every secret will be detected.


---

Commands only

cpt --commands-only

Attempts to return only detected shell commands.


---

Output only

cpt --output-only

Attempts to return terminal output without shell commands.


---

AI formatted output

cpt --ai

Formats the captured terminal content for use with AI tools and debugging workflows.


---

Explicit session

For diagnostics or advanced usage:

cpt --session-id SESSION_ID

Example:

cpt --session-id sess_example

An explicit session ID takes priority over automatic session detection.


---

Capture Modes

CopyTerm uses several capture sources.

1. IDE Terminal Bridge

Used when running inside a supported IDE terminal.

The bridge can provide the terminal emulator's retained buffer, including historical scrollback.

This is the preferred method when available.

2. tmux

When running inside tmux, CopyTerm can capture the active tmux pane.

Example:

cpt

No additional command is required when CopyTerm detects the tmux environment.

3. Shell Session Buffer

Shell integration records terminal activity into a session-specific buffer.

This allows CopyTerm to capture content that was recorded by the shell integration.

4. Platform Console

On Windows, CopyTerm can use the Windows Console API as a fallback.

The amount of available history depends on the console and terminal configuration.


---

The Capture Epoch Model

clear and cls have special meaning in CopyTerm.

They are treated as capture boundaries.

They do not mean that CopyTerm deletes the terminal emulator's own scrollback.

Instead, CopyTerm records where the new capture epoch starts.

For example:

BEFORE_CLEAR_001
BEFORE_CLEAR_002

clear

AFTER_CLEAR_001
AFTER_CLEAR_002

After the clear, running:

cpt

should capture:

AFTER_CLEAR_001
AFTER_CLEAR_002

The old content is excluded.


---

Epoch 0

If the user has never run clear or cls in the current CopyTerm session, the capture is in:

Epoch 0

In this state, CopyTerm can use the complete available capture source.


---

After clear

After a clear:

Epoch 0
    |
    | clear
    v
Epoch 1

Another clear:

Epoch 1
    |
    | clear
    v
Epoch 2

Only the latest epoch is considered for normal capture.


---

Empty epoch

This is important.

If the user runs:

clear

and immediately runs:

cpt --stdout

without producing any new output, CopyTerm should return an empty capture.

It must not bring back content from before the clear.


---

Text containing "clear"

CopyTerm does not treat every occurrence of the word clear as a clear command.

For example:

echo "clear"

must not create a new capture epoch.

Likewise:

echo "this output contains the word clear"

must not create a new epoch.

Only the actual configured clear operation should advance the capture epoch.


---

Terminal Isolation

CopyTerm is designed to keep terminal sessions separate.

For example, suppose three terminals contain:

Terminal 1:
TERMINAL_01

Terminal 2:
TERMINAL_02

Terminal 3:
TERMINAL_03

Running:

cpt

in Terminal 1 should capture Terminal 1's session.

It should not return:

TERMINAL_02
TERMINAL_03

CopyTerm uses session information and process relationships to associate a command with its terminal.

It does not use the newest buffer as a replacement for proper session identification.


---

IDE Terminal Bridge

CopyTerm includes an IDE terminal bridge for supported environments such as VS Code based terminals and Antigravity.

The bridge exists because terminal emulator history is normally owned by the terminal emulator itself.

A child process such as:

python copyterm.py

cannot normally ask the terminal emulator:

Give me all 5,000 lines of your scrollback.

The IDE bridge provides a controlled interface for supported terminals.

The general flow is:

IDE Terminal
     |
     v
xterm.js terminal buffer
     |
     v
CopyTerm IDE Bridge
     |
     v
cpt
     |
     v
clipboard / stdout / file

When the bridge is available, CopyTerm can capture historical terminal content that would otherwise be inaccessible.


---

Check bridge status

Run:

cpt doctor

A working bridge should report information similar to:

[IDE Terminal Bridge]
    Detected: YES
    Bridge Status: CONNECTED
    Historical Scrollback: AVAILABLE

The exact output depends on the IDE and terminal environment.


---

Test the bridge

Inside the supported IDE terminal:

cpt bridge-test

If the bridge is not detected:

1. Make sure the IDE is running.


2. Make sure the CopyTerm bridge extension is installed.


3. Restart or reload the IDE.


4. Open a new integrated terminal.


5. Run:



cpt doctor

Then:

cpt bridge-test


---

Configuration and Runtime Files

CopyTerm keeps runtime data outside the project directory.

Default runtime directory:

~/.copyterm

On Windows:

%USERPROFILE%\.copyterm

A typical structure is:

~/.copyterm/
|
+-- bin/
|   +-- cpt
|   +-- copyterm
|   +-- copyterm.py
|
+-- sessions/
|   +-- <session>.buf
|   +-- <session>.epoch
|
+-- extensions/
|
+-- services/

The exact files depend on the platform and installed integrations.

Runtime session files should not be committed to Git.

They can contain terminal activity and should be treated as local runtime data.


---

Troubleshooting

cpt command is not found

First check:

which cpt

On PowerShell:

Get-Command cpt

If it is not found, open a new terminal after installation.

On Windows, also check:

Get-Command copyterm


---

Check CopyTerm installation

Run:

cpt doctor

This is the first command to use when troubleshooting.


---

cpt --stdout prints nothing

Check the active session:

cpt doctor

Then check that the shell integration reports an active capture session.

On Windows, inspect:

Get-ChildItem "$HOME\.copyterm\sessions"

Do not delete session files while the shell is actively using them.


---

Clipboard copy fails

Run:

cpt --stdout

If stdout contains the expected content but cpt does not update the clipboard, the capture itself is working and the problem is likely platform clipboard access.

On Linux, make sure the required clipboard utility is available, such as:

wl-copy

or:

xclip
xsel


---

IDE bridge is not detected

Run:

cpt doctor

If it reports:

Bridge Status: NOT RUNNING

make sure you are running the command inside a supported IDE terminal and that the CopyTerm bridge extension is installed.

Then reload the IDE and open a new terminal.


---

clear does not behave as expected

Run:

cpt doctor

Check the current epoch.

For a basic test:

OLD_OUTPUT

Run:

clear

Then:

NEW_OUTPUT

Finally:

cpt --stdout

Only the current epoch should be returned.


---

PowerShell profile problems

CopyTerm adds a managed integration block to supported PowerShell profiles.

If installation has been interrupted or the profile contains an old CopyTerm integration, reinstalling should update the managed section instead of replacing the entire profile.

Do not manually delete unrelated PowerShell profile configuration.


---

CMD starts too many processes

CopyTerm does not require CMD AutoRun.

If you previously configured CopyTerm through CMD AutoRun, remove the old CopyTerm AutoRun entry and restart the terminal.

Check:

Get-ItemProperty `
    "HKCU:\Software\Microsoft\Command Processor" `
    -ErrorAction SilentlyContinue

CopyTerm should not install a recursive CMD AutoRun configuration.


---

Development

Clone the repository:

git clone https://github.com/0xSatish/Copyterm.git
cd Copyterm

Check the repository:

git status

Run the Python core directly:

python src/copyterm.py --help

Run:

python src/copyterm.py version


---

Running tests

Run the available test suite from the repository.

For Python tests:

pytest

If the project contains platform-specific tests, run the tests appropriate for your operating system.

Before submitting changes, also check:

git diff --check


---

Project Structure

Copyterm/
|
+-- src/
|   +-- copyterm.py
|   +-- core/
|   +-- cli/
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

The project contains both Python and C++ components. The Python engine provides the main cross-platform capture logic, while the C++ components support platform and project-specific functionality.


---

Design Principles

CopyTerm follows a few basic rules.

Current terminal first

Capture the terminal that ran cpt, not an unrelated terminal.

No global transcript

Each terminal should have its own session.

No working-directory dependency

This should work:

cd /tmp
cpt

and:

cd ~/project
cpt

The active terminal should remain the same.

No recursive shells

CopyTerm should not create a chain of shell processes just to provide command integration.

Clear means a capture boundary

A clear operation starts a new CopyTerm capture epoch.

It does not need to destroy the terminal emulator's scrollback.

Bridge when available

When a supported IDE can provide real terminal scrollback, CopyTerm should use it instead of pretending that a shell transcript is the same thing.


---

Security

CopyTerm works with terminal content, so captured data may contain sensitive information.

For this reason:

Runtime session files are stored locally.

Terminal contents are not intentionally sent to a remote service by the core capture engine.

Debug logs should not contain terminal contents.

Authentication tokens used by the IDE bridge are stored in local runtime configuration.

Clipboard contents are controlled by the operating system.

--redact can be used to mask common secret and token patterns.


Example:

cpt --redact

Redaction is not guaranteed to detect every possible secret. Review captured output before sharing it publicly.


---

Performance and Process Safety

CopyTerm is designed to avoid unnecessary background processes.

In particular, the Windows integration does not use CMD AutoRun.

A normal:

cpt

should not create an uncontrolled chain of:

cmd.exe
cmd.exe
cmd.exe
cmd.exe
...

Session capture should read only the relevant terminal session.

Large terminal histories should be handled without repeatedly scanning unrelated terminal sessions.


---

Limitations

CopyTerm cannot overcome limitations imposed by the terminal environment.

In particular:

1. A normal child process cannot generally access another terminal emulator's private historical scrollback.


2. IDE bridge support depends on the IDE exposing its terminal buffer.


3. Shell integration only captures information available through the shell integration.


4. Console history limits depend on the terminal emulator and operating system.


5. Secret redaction is pattern based and is not a complete security system.


6. --commands-only and --output-only rely on detecting shell prompts and command structure, so unusual shell configurations may produce imperfect results.




---

Example Workflow

A common debugging workflow looks like this:

$ make
...
compiler output
...

$ ./my_application
...
application output
...

$ cpt
Copied terminal history to clipboard.

Paste the result into your issue tracker or AI assistant.

For a file:

cpt --save debug-output.txt

For scripts:

cpt --stdout > debug-output.txt

For the last part of the terminal:

cpt --last 100

For output that may contain credentials:

cpt --redact


---

Version

Check the installed version with:

cpt version

or:

cpt --version


---

Contributing

Contributions are welcome.

Before opening a pull request:

1. Keep changes focused.


2. Do not commit runtime session files.


3. Do not commit terminal output containing secrets.


4. Run the available tests.


5. Run:



git diff --check

6. Test shell integrations on the platform you changed.


7. Document platform-specific behavior when necessary.



For changes involving terminal capture, test both normal capture and:

cpt --stdout

For changes involving clear or cls, test the capture epoch behavior.

For changes involving Windows installation, test the installer from a fresh checkout.


---

License

CopyTerm is released under the MIT License.

See LICENSE for the full license text.  - [Universal Python Installer](#universal-python-installer)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Capture Modes](#capture-modes)
- [The Capture Epoch Model](#the-capture-epoch-model)
- [Terminal Isolation](#terminal-isolation)
- [IDE Terminal Bridge](#ide-terminal-bridge)
- [Configuration and Runtime Files](#configuration-and-runtime-files)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Security](#security)
- [Project Structure](#project-structure)
- [License](#license)

---

## Key Features

- Capture terminal history with `cpt`
- Copy the captured content directly to the clipboard
- Print the captured content with `cpt --stdout`
- Save terminal content to a file
- Capture only the last N lines
- Capture commands only
- Capture output only
- Remove ANSI terminal escape sequences by default
- Optional raw terminal output
- Optional secret and token redaction
- Per-terminal session isolation
- Capture epoch support for `clear` and `cls`
- Historical scrollback support through the IDE bridge
- tmux pane capture support
- Works independently of the current working directory
- Windows, Linux, and macOS support
- No external Python packages required by the core engine

---

## Why CopyTerm

A terminal can contain much more information than what is currently visible.

For example:

```text
$ make
...
hundreds of lines of compiler output
...
$ ./app
...
application output
...
