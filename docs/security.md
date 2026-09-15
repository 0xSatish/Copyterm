# COPYTERM Security Architecture & Threat Model

## 1. Core Security Principles

`copyterm` is designed under a strict **Zero-Trust Local-First** security philosophy:

1. **Zero Network Connectivity:**  
   `copyterm` does not contain any HTTP, TCP, UDP, or socket clients. It never connects to the internet, cloud APIs, or analytics servers.
2. **Zero Default Logging:**  
   `copyterm` does not log clipboard content to system event logs or third-party telemetry tools.
3. **No Elevated Privileges Required:**  
   `copyterm` runs completely within standard unprivileged user space. It never requires Administrator/root rights.

---

## 2. Threat Model & Mitigations

### Threat A: Cross-Session Data Leakage
- **Risk:** In an environment with 30+ terminals, sensitive commands or tokens entered in Terminal A could appear when running `copyterm` in Terminal B.
- **Mitigation:** Every session is tied to a distinct, high-entropy `COPYTERM_SESSION_ID` and verified through parent process tree matching. The underlying storage files (`.buf` and `.meta`) are strictly separated per session ID. Cross-contamination tests verify 0% leakage across 30+ terminals.

### Threat B: Local Multi-User Access
- **Risk:** Other local users on a shared multi-tenant server (e.g. shared Linux host or Windows server) attempt to read another user's session buffer in `~/.copyterm/sessions/`.
- **Mitigation:**
  - On POSIX: `~/.copyterm` is created with strict `0700` (`rwx------`) permissions. Session files inherit `0600` (`rw-------`).
  - On Windows: Directory permissions inherit the user's private `%USERPROFILE%` ACLs, preventing access by other standard users.

### Threat C: Accidental Secret Leakage into Clipboard
- **Risk:** Terminal output containing AWS credentials, API keys, or private keys is placed into the clipboard and pasted into public channels.
- **Mitigation:**
  - Optional `--redact` flag provides automated regex pattern scanning for:
    - AWS Access Keys (`AKIA...`)
    - GitHub Personal Access Tokens (`ghp_...`, `github_pat_...`)
    - RSA/EC/OpenSSH Private Keys
    - JWT and Bearer Authorization Tokens
    - Password assignments in scripts and commands.

### Threat D: Shell Profile Corruption
- **Risk:** `copyterm install` corrupts `~/.bashrc` or `$PROFILE`, making the user's terminal unusable.
- **Mitigation:**
  - All profile edits create automatic timestamped backups (e.g. `profile.bak.<timestamp>`) prior to writing.
  - Integration blocks use clearly bounded comment markers (`# >>> copyterm shell integration >>>`).
  - `copyterm uninstall` performs safe, non-destructive removal of only the demarcated block.
  - The shell hooks use fail-safe constructs (`2>/dev/null`, `-ErrorAction SilentlyContinue`) so any failure in copyterm never halts the user's shell.

---

## 3. Storage Lifetime & Cleanup

- **Session Retention:** Inactive sessions older than 24 hours are automatically flagged as stale.
- **Process Liveness Verification:** During resolution and cleanup, `copyterm` verifies whether the shell PID is still alive. If dead, the session is eligible for immediate purging via `copyterm clean-sessions`.
- **Size Bounds:** Configurable circular ring buffer limits prevent unbounded disk consumption.
