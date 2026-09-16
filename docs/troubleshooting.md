# COPYTERM (`cpt`) Troubleshooting Guide

This guide covers common issues, diagnostic steps, and resolutions for `cpt`.

---

## 1. Diagnostics First: `cpt doctor`

Whenever you encounter unexpected behavior, run:
```bash
cpt doctor
```
This prints a comprehensive report of:
- Command: `cpt` (alias: `copyterm`)
- Current OS and detected shell
- Parent process PID and process ancestors
- Current Session ID and Capture Epoch
- Boundary Tracking availability
- IDE Terminal Bridge status (Connected, Protocol version, Historical scrollback)
- tmux session status
- Clipboard backend status (AVAILABLE or UNAVAILABLE)

For live buffer capture testing:
```bash
cpt doctor --bridge-test
```

---

## 2. Common Issues & Solutions

### Issue A: `Historical scrollback: UNAVAILABLE` in Antigravity / VS Code
**Cause:** The CopyTerm IDE Bridge extension is not installed or the extension host has not loaded it.  
**Resolution:**
1. Run:
   ```bash
   cpt install ide
   ```
2. Reload your IDE window (Press `Ctrl+Shift+P` -> `Developer: Reload Window`).
3. Run `cpt doctor` to verify:
   ```text
   [IDE Terminal Bridge]
     Detected:                 YES
     IDE:                      Antigravity
     Terminal Implementation:  xterm.js
     Bridge Status:            CONNECTED (Ping OK)
     Historical Scrollback:    AVAILABLE
     Boundary Tracking:        AVAILABLE
   ```

---

### Issue B: `clear` was run but old history was still captured
**Cause:** The shell session was launched before the updated integration script was sourced.  
**Resolution:**
1. Reload your shell profile or open a new terminal:
   - PowerShell: `. $PROFILE` or `. .\integrations\powershell\copyterm.ps1`
   - Bash: `source ~/.bashrc`
   - Zsh: `source ~/.zshrc`
2. Run `cpt doctor` to verify that `Current Epoch` increments after typing `clear` or `cls`.

---

### Issue C: `cpt --stdout` produces no output
**Cause:** 
1. If `clear` was run immediately before `cpt` with no intervening output, the current epoch is legitimately empty (0 lines).
2. If using PowerShell pipeline redirection, ensure you use `cpt --stdout > capture.txt` or `cpt --stdout | Out-String`.

---

### Issue D: `Clipboard error: No supported clipboard tool found` (Linux)
**Cause:** Minimal Linux window managers or headless servers may lack clipboard utilities.  
**Resolution:**
- On Wayland: Install `wl-clipboard` (`sudo apt install wl-clipboard`).
- On X11: Install `xclip` or `xsel` (`sudo apt install xclip`).
- Alternatively, use stdout or save mode: `cpt --stdout > output.txt` or `cpt -s session.txt`.

---

### Issue E: Clean Uninstallation
**Resolution:**
To cleanly remove all shell hooks and IDE extensions:
```bash
cpt uninstall all
```
