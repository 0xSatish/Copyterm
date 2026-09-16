# COPYTERM Security Architecture & Threat Model

## 1. Core Security Principles

`copyterm` is designed under a strict **Zero-Trust Local-First** security philosophy:

1. **Zero External Network Connectivity:**  
   `copyterm` does not connect to the internet, cloud APIs, analytics servers, or remote hosts.
2. **Zero Default Logging:**  
   `copyterm` does not log terminal buffer content to disk logs or extension logs.
3. **No Elevated Privileges Required:**  
   `copyterm` runs completely within standard unprivileged user space.
4. **Localhost-Only IPC:**  
   The IDE Terminal Bridge communicates exclusively over user-restricted Windows Named Pipes or POSIX Unix Domain Sockets (`0600`). It never binds to `0.0.0.0` or TCP ports.

---

## 2. Threat Model & Mitigations

### Threat A: Unauthorized Local Process Interception
- **Risk:** An unprivileged local process attempts to query the IDE Bridge endpoint to inspect terminal buffer text.
- **Mitigation:**
  - On startup, the IDE Bridge generates a cryptographically random 256-bit authentication token (`crypto.randomBytes(24)`).
  - The discovery file `~/.copyterm/ide_bridge.json` is created with strict file permissions (`0600`).
  - Every IPC request must include the matching `auth_token`. Requests with missing or forged tokens are immediately rejected with `401 Unauthorized`.
  - Windows Named Pipes are created with DACLs matching the active user session.

### Threat B: Cross-Terminal Isolation & PID Spoofing
- **Risk:** Terminal A's `copyterm` invocation receives Terminal B's scrollback.
- **Mitigation:**
  - The bridge maps `caller_pid` strictly to `terminal.processId`.
  - If 0 terminals match, the request fails with an error.
  - If multiple terminals match, the request fails with an ambiguity error.
  - The bridge never guesses the active terminal on unmatched PIDs.

### Threat C: Accidental Secret Leakage into Clipboard
- **Risk:** Terminal output containing AWS credentials, API keys, or private keys is placed into the clipboard and pasted into public channels.
- **Mitigation:**
  - Optional `--redact` flag provides automated regex pattern scanning for:
    - AWS Access Keys (`AKIA...`)
    - GitHub Personal Access Tokens (`ghp_...`, `github_pat_...`)
    - RSA/EC/OpenSSH Private Keys
    - JWT and Bearer Authorization Tokens
    - Passwords and secret assignments.

### Threat D: Clipboard Overwrite During Internal Capture
- **Risk:** Internal workbench copy actions overwrite the user's prior clipboard text without their permission.
- **Mitigation:**
  - The IDE Bridge saves the user's current clipboard text before executing serialization.
  - After reading the terminal buffer, it immediately restores the user's original clipboard.
  - `copyterm` CLI is the sole entity that places the final processed output onto the clipboard.

---

## 3. Storage Lifetime & Cleanup

- **Session Retention:** Inactive sessions older than 24 hours are automatically flagged as stale.
- **IPC Cleanup:** Discovery files and socket endpoints are unlinked on extension shutdown (`deactivate()`).
- **Disk Bounds:** Fallback ring buffers are bounded to 10 MB per session.
