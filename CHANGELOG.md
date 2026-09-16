# Changelog

All notable changes to the `copyterm` (`cpt`) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-16

### Added
- **Canonical Short Command `cpt`**: Introduced `cpt` as the primary user-facing command across PowerShell, Bash, Zsh, CMD, and native binary distributions (`cpt.exe`), while preserving `copyterm` as a fully backward-compatible alias.
- **Active Terminal Session Capture & Slicing Repair**:
  - Fixed session resolution to strictly match integer process IDs against process ancestors and prevent parent PID collisions across multiple terminals.
  - Configured explicit Win32 `ctypes` 64-bit parameter prototypes (`argtypes`/`restype`) for `CreateFileW`, `SetFilePointer`, `ReadFile`, and `CloseHandle` to eliminate 64-bit handle truncation on x64 Windows.
  - Eliminated double byte offset slicing between `SessionManager.read_buffer` and `EpochManager.slice_buffer_by_epoch`.
  - Added `utf-8-sig` decoding tolerance to seamlessly parse `.epoch` and `.meta` files written with UTF-8 byte order marks (BOM) by Windows PowerShell 5.1.
- **PowerShell Session Isolation & Flush Guarantee**:
  - Configured child PowerShell processes to detect parent PID divergence and initialize independent sessions.
  - Added synchronous host console flushing in `cpt` and `Clear-Host` hooks before recording byte offsets to ensure pre-clear outputs are committed to disk.
- **Installer Syntax & Profile Block Management**:
  - Repaired missing closing bracket `}` in `install.ps1` profile iteration block.
  - Verified 100% parse and execution safety across all PowerShell integration scripts.
- **Capture Epoch Model (`clear` as a Copy Boundary)**:
  - When `clear` (or `cls`, `Clear-Host`) is executed, the shell integration establishes a new CopyTerm Capture Epoch (`epoch += 1`).
  - `cpt` captures only output belonging to the current epoch (lines produced after the latest `clear`).
  - All retained scrollback produced *after* `clear` is preserved and captured in full (not restricted to visible viewport).
  - Pre-clear content is strictly excluded from the captured payload.
  - If `clear` was never executed (`epoch == 0`), 100% retroactive scrollback from before CopyTerm started is captured.
  - Slicing is echo-safe: commands like `echo "clear"` or printed text containing "clear" do NOT reset the epoch.
  - Multiple `clear` commands properly pick the latest epoch boundary.
  - Empty post-clear state returns 0 lines and never falls back to pre-clear history.
  - **Lock-Free Concurrency Architecture**: Decoupled epoch metadata state (`.epoch`) from live capture stream buffers (`.buf`), eliminating Windows file-locking constructor exceptions during `clear` / `Clear-Host`.
  - **CMD Process Safety**: Eliminated subprocess spawning during CMD shell startup and disabled default registry AutoRun hook to prevent recursive `cmd.exe` process explosion.
- **`cpt --stdout` Fix & Exact Parity**: Fixed standard output streaming to ensure exact parity between clipboard and stdout capture results without mutating clipboard during stdout-only execution.
- **Per-Terminal Isolation with Epochs**: Ensured that clearing Terminal A only increments Terminal A's epoch and never impacts Terminal B.
- **Enhanced Diagnostics (`cpt doctor`)**: Added display of Command (`cpt`), Session ID, Current Epoch, and Boundary Tracking availability.

---

## [1.0.0] - Initial Production Release

### Added
- **Core Engine:** Standalone, single-binary C++17 and Python engine with zero external runtime dependencies.
- **Strict Per-Session Isolation:** Multi-tier session resolver hierarchy guaranteeing 100% isolation across 30+ concurrent terminals.
- **IDE Terminal Bridge:** Authenticated local IPC bridge to xterm.js renderer in Antigravity IDE and VS Code for true historical buffer capture.
- **Bounded Ring Buffer:** File-backed circular ring buffer with 10 MB default limit.
- **ANSI & VT Sanitizer:** Full ANSI/VT escape sequence stripper with progress bar normalization.
- **Secret Redaction:** High-speed credential detection and masking (`--redact`) for AWS keys, GitHub tokens, JWTs, and passwords.
- **Multi-Platform Clipboard Subsystem:** Win32 native API, Wayland `wl-copy`, X11 `xclip`/`xsel`, and ANSI OSC 52 sequence generation.
