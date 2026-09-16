#!/usr/bin/env bash
# ==============================================================================
# COPYTERM — POSIX Uninstaller
# ==============================================================================

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$REPO_ROOT/install.sh" ]; then
    exec "$REPO_ROOT/install.sh" --uninstall "$@"
elif [ -f "$REPO_ROOT/install.py" ]; then
    exec python3 "$REPO_ROOT/install.py" --uninstall "$@"
fi
