#!/usr/bin/env bash
# ==============================================================================
# COPYTERM — Bash Integration Script
# ==============================================================================

if [ -z "$COPYTERM_SESSION_ID" ]; then
    _ts=$(date +%s%3N 2>/dev/null || date +%s)
    _rnd=$(head -c 16 /dev/urandom 2>/dev/null | md5sum | head -c 6 || echo "$$")
    export COPYTERM_SESSION_ID="sess_${_ts}_${$}_${_rnd}"
fi

__copyterm_data_dir="${COPYTERM_DATA_DIR:-$HOME/.copyterm}"
__copyterm_sessions_dir="$__copyterm_data_dir/sessions"
mkdir -p "$__copyterm_sessions_dir" 2>/dev/null

__copyterm_buf_file="$__copyterm_sessions_dir/${COPYTERM_SESSION_ID}.buf"
__copyterm_meta_file="$__copyterm_sessions_dir/${COPYTERM_SESSION_ID}.meta"

# Write session metadata
cat <<EOF > "$__copyterm_meta_file" 2>/dev/null
session_id=$COPYTERM_SESSION_ID
shell_name=bash
pid=$$
ppid=$PPID
cwd=$PWD
tty=$(tty 2>/dev/null || echo "unknown")
start_time_ms=$(date +%s%3N 2>/dev/null || date +%s)
last_active_time_ms=$(date +%s%3N 2>/dev/null || date +%s)
backend=shell_integration
EOF

# Start Output Capture via stream tee
if [ -z "$__COPYTERM_CAPTURE_ACTIVE" ]; then
    export __COPYTERM_CAPTURE_ACTIVE=1
    exec > >(tee -a "$__copyterm_buf_file") 2>&1
fi

copyterm() {
    python3 "C:/Users/satis/OneDrive/Desktop/Copyterm/src/copyterm.py" "$@" 2>/dev/null || \
    python "C:/Users/satis/OneDrive/Desktop/Copyterm/src/copyterm.py" "$@" 2>/dev/null || \
    "C:/Users/satis/OneDrive/Desktop/Copyterm/copyterm.exe" "$@"
}
