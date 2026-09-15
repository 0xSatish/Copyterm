# COPYTERM Troubleshooting Guide

This guide covers common issues, diagnostic steps, and resolutions.

---

## 1. Diagnostics First: `copyterm doctor`

Whenever you encounter unexpected behavior, run:
```bash
copyterm doctor
```
This prints a comprehensive report of:
- Current OS and detected shell
- Parent process PID and terminal emulator
- Clipboard backend status (AVAILABLE or UNAVAILABLE)
- Resolved session ID and capture buffer size
- Total active sessions count on disk

---

## 2. Common Issues & Solutions

### Issue A: `No active capture session detected for this terminal`
**Cause:** The shell instance was started without `copyterm` integration installed, or the shell profile was not reloaded after installation.  
**Resolution:**
1. Run `copyterm install` (or `copyterm install powershell` / `copyterm install bash`).
2. Reload your profile or open a new terminal:
   - PowerShell: `. $PROFILE`
   - Bash: `source ~/.bashrc`
   - Zsh: `source ~/.zshrc`
3. Verify that `$env:COPYTERM_SESSION_ID` (PowerShell) or `$COPYTERM_SESSION_ID` (Bash/Zsh) is populated.

---

### Issue B: `Clipboard error: No supported clipboard tool found` (Linux)
**Cause:** Linux systems running minimal window managers or headless servers may lack clipboard utilities.  
**Resolution:**
- On Wayland: Install `wl-clipboard` (`sudo apt install wl-clipboard` or `sudo dnf install wl-clipboard`).
- On X11: Install `xclip` or `xsel` (`sudo apt install xclip`).
- Alternatively, use file mode: `copyterm -s session.txt` or pipe: `copyterm --stdout > output.txt`.

---

### Issue C: Output contains unexpected progress bar fragments
**Cause:** Raw mode was used on tools that emit carriage returns (`\r`).  
**Resolution:**
- Run standard clean mode: `copyterm` (or `copyterm --clean`).
- `copyterm`'s line simulation state machine collapses `\r` overwrite sequences into the final clean line.

---

### Issue D: Historical output prior to shell startup is missing
**Cause:** Standard terminal emulators (Windows Terminal, GNOME Terminal, Alacritty) do not permit child CLI processes to retroactively query historical scrollback generated before capture integration was active.  
**Resolution:**
- `copyterm` records continuously from the moment the shell is opened.
- In `tmux`, full scrollback history is always available via `tmux capture-pane`.

---

### Issue E: Reverting / Uninstalling Shell Integration
**Resolution:**
To cleanly remove all added hooks from your shell profiles without touching other settings:
```bash
copyterm uninstall
```
Backup copies (`*.bak.<timestamp>`) are preserved in the same directory.
