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
