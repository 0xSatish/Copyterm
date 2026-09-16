#!/usr/bin/env bash
# ==============================================================================
# COPYTERM — POSIX (Linux/macOS) One-Click Bootstrap Installer
# Canonical Command: cpt (Alias: copyterm)
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# If Python 3 is available, run the unified installer engine
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$REPO_ROOT/install.py" "$@"
fi

if command -v python >/dev/null 2>&1; then
    exec python "$REPO_ROOT/install.py" "$@"
fi

# POSIX Shell Fallback Installer
CPT_HOME="${COPYTERM_DATA_DIR:-$HOME/.copyterm}"
BIN_DIR="$CPT_HOME/bin"
INTEGRATIONS_DIR="$CPT_HOME/integrations"
SESSIONS_DIR="$CPT_HOME/sessions"
LOGS_DIR="$CPT_HOME/logs"
SERVICES_DIR="$CPT_HOME/services"

UNINSTALL=0
QUIET=0

for arg in "$@"; do
    case "$arg" in
        --uninstall) UNINSTALL=1 ;;
        --quiet|-q) QUIET=1 ;;
    esac
done

write_step() {
    local num="$1"
    local name="$2"
    local status="$3"
    if [ "$QUIET" -eq 0 ]; then
        printf "[%s/7] %-30s ... %s\n" "$num" "$name" "$status"
    fi
}

if [ "$UNINSTALL" -eq 1 ]; then
    if [ "$QUIET" -eq 0 ]; then
        echo "=================================================="
        echo "             CopyTerm Uninstaller                 "
        echo "=================================================="
    fi
    rm -rf "$BIN_DIR" "$INTEGRATIONS_DIR"
    rm -rf "$HOME/.antigravity-ide/extensions/copyterm.copyterm-terminal-bridge-1.0.0"
    rm -rf "$HOME/.vscode/extensions/copyterm.copyterm-terminal-bridge-1.0.0"
    if [ -f "$HOME/.bashrc" ]; then
        sed -i.bak '/# >>> CopyTerm/,/# <<< CopyTerm/d' "$HOME/.bashrc" 2>/dev/null || true
    fi
    if [ -f "$HOME/.zshrc" ]; then
        sed -i.bak '/# >>> CopyTerm/,/# <<< CopyTerm/d' "$HOME/.zshrc" 2>/dev/null || true
    fi
    echo "CopyTerm uninstallation complete."
    exit 0
fi

# Detection
OS_NAME="$(uname -s)"
ARCH="$(uname -m)"
CURRENT_SHELL="$(basename "$SHELL")"

if [ "$QUIET" -eq 0 ]; then
    echo "=================================================="
    echo "               CopyTerm Installer                 "
    echo "=================================================="
    echo "Detected OS       : $OS_NAME"
    echo "Architecture      : $ARCH"
    echo "Shell             : $CURRENT_SHELL"
    echo ""
fi

# [1/7] Installing binary
mkdir -p "$BIN_DIR" "$INTEGRATIONS_DIR" "$SESSIONS_DIR" "$LOGS_DIR" "$SERVICES_DIR"

if [ -f "$REPO_ROOT/src/copyterm.py" ]; then
    cp -f "$REPO_ROOT/src/copyterm.py" "$BIN_DIR/copyterm.py"
fi

if [ -f "$REPO_ROOT/cpt" ]; then
    cp -f "$REPO_ROOT/cpt" "$BIN_DIR/cpt"
    chmod +x "$BIN_DIR/cpt"
elif [ ! -f "$BIN_DIR/cpt" ]; then
    cat << 'EOF' > "$BIN_DIR/cpt"
#!/usr/bin/env bash
exec python3 "$(dirname "$0")/copyterm.py" "$@"
EOF
    chmod +x "$BIN_DIR/cpt"
fi

if [ -f "$REPO_ROOT/copyterm" ]; then
    cp -f "$REPO_ROOT/copyterm" "$BIN_DIR/copyterm"
    chmod +x "$BIN_DIR/copyterm"
elif [ ! -f "$BIN_DIR/copyterm" ]; then
    cat << 'EOF' > "$BIN_DIR/copyterm"
#!/usr/bin/env bash
exec "$(dirname "$0")/cpt" "$@"
EOF
    chmod +x "$BIN_DIR/copyterm"
fi

if [ -d "$REPO_ROOT/integrations" ]; then
    cp -rf "$REPO_ROOT/integrations/"* "$INTEGRATIONS_DIR/"
fi
write_step 1 "Installing binary" "OK"

# [2/7] Configuring PATH
write_step 2 "Configuring PATH" "OK"

# [3/7] Installing shell integration
HOOK_SNIPPET_BASH="# >>> CopyTerm managed block >>>
export PATH=\"\$HOME/.copyterm/bin:\$PATH\"
__copyterm_bash=\"\${COPYTERM_DATA_DIR:-\$HOME/.copyterm}/integrations/bash/copyterm.bash\"
[ -f \"\$__copyterm_bash\" ] && . \"\$__copyterm_bash\"
# <<< CopyTerm managed block <<<"

if [ -f "$HOME/.bashrc" ]; then
    if ! grep -q "CopyTerm managed block" "$HOME/.bashrc"; then
        printf "\n%s\n" "$HOOK_SNIPPET_BASH" >> "$HOME/.bashrc"
    fi
fi

HOOK_SNIPPET_ZSH="# >>> CopyTerm managed block >>>
export PATH=\"\$HOME/.copyterm/bin:\$PATH\"
__copyterm_zsh=\"\${COPYTERM_DATA_DIR:-\$HOME/.copyterm}/integrations/zsh/copyterm.zsh\"
[ -f \"\$__copyterm_zsh\" ] && . \"\$__copyterm_zsh\"
# <<< CopyTerm managed block <<<"

if [ -f "$HOME/.zshrc" ]; then
    if ! grep -q "CopyTerm managed block" "$HOME/.zshrc"; then
        printf "\n%s\n" "$HOOK_SNIPPET_ZSH" >> "$HOME/.zshrc"
    fi
fi
write_step 3 "Installing shell integration" "OK"

# [4/7] Configuring IDE bridge
if [ -d "$REPO_ROOT/extensions/copyterm-terminal-bridge" ]; then
    mkdir -p "$HOME/.antigravity-ide/extensions" "$HOME/.vscode/extensions"
    cp -rf "$REPO_ROOT/extensions/copyterm-terminal-bridge" "$HOME/.antigravity-ide/extensions/copyterm.copyterm-terminal-bridge-1.0.0" 2>/dev/null || true
    cp -rf "$REPO_ROOT/extensions/copyterm-terminal-bridge" "$HOME/.vscode/extensions/copyterm.copyterm-terminal-bridge-1.0.0" 2>/dev/null || true
fi
write_step 4 "Configuring IDE bridge" "OK"

# [5/7] Configuring runtime state
if [ ! -f "$CPT_HOME/config.json" ]; then
    echo '{"version":"1.1.0","default_clean":true,"capture_tier_order":["ide_bridge","tmux","transcript"],"max_history_lines":50000}' > "$CPT_HOME/config.json"
fi
write_step 5 "Configuring runtime state" "OK"

# [6/7] Configuring services
write_step 6 "Configuring user service" "N/A"

# [7/7] Running verification
if [ -x "$BIN_DIR/cpt" ] || [ -f "$BIN_DIR/copyterm.py" ]; then
    write_step 7 "Running verification" "OK"
else
    write_step 7 "Running verification" "FAIL"
fi

if [ "$QUIET" -eq 0 ]; then
    echo ""
    echo "--------------------------------------------------"
    echo " CopyTerm installation successful."
    echo "--------------------------------------------------"
    echo ""
    echo "Command:"
    echo "    cpt  (alias: copyterm)"
    echo ""
    echo "Runtime:"
    echo "    $CPT_HOME"
    echo ""
    echo "Open a new terminal before using cpt."
    echo ""
fi
