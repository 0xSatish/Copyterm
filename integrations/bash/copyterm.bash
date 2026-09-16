#!/usr/bin/env bash
# ==============================================================================
# COPYTERM — Bash Integration Script
# Canonical Short Command: cpt (Alias: copyterm)
# Clear establishes a Capture Epoch boundary
# CWD-Independent Architecture: Works from any working directory
# ==============================================================================

if [ -z "$COPYTERM_SESSION_ID" ]; then
    _ts=$(date +%s%3N 2>/dev/null || date +%s)
    _rnd=$(head -c 16 /dev/urandom 2>/dev/null | md5sum | head -c 6 || echo "$$")
    export COPYTERM_SESSION_ID="sess_${_ts}_${$}_${_rnd}"
fi

export __copyterm_epoch=0
__copyterm_data_dir="${COPYTERM_DATA_DIR:-$HOME/.copyterm}"
__copyterm_sessions_dir="$__copyterm_data_dir/sessions"
mkdir -p "$__copyterm_sessions_dir" 2>/dev/null

__copyterm_buf_file="$__copyterm_sessions_dir/${COPYTERM_SESSION_ID}.buf"
__copyterm_meta_file="$__copyterm_sessions_dir/${COPYTERM_SESSION_ID}.meta"
__copyterm_epoch_file="$__copyterm_sessions_dir/${COPYTERM_SESSION_ID}.epoch"

# Write session metadata
cat <<EOF > "$__copyterm_meta_file" 2>/dev/null
session_id=$COPYTERM_SESSION_ID
shell_name=bash
pid=$$
ppid=$PPID
tty=$(tty 2>/dev/null || echo "unknown")
start_time_ms=$(date +%s%3N 2>/dev/null || date +%s)
last_active_time_ms=$(date +%s%3N 2>/dev/null || date +%s)
backend=shell_integration
EOF

# Write initial epoch state
printf '{"session_id":"%s","epoch_id":0,"clear_count":0,"last_clear_timestamp_ms":0,"latest_boundary_token":""}\n' \
    "$COPYTERM_SESSION_ID" > "$__copyterm_epoch_file" 2>/dev/null

# Start Output Capture via stream tee
if [ -z "$__COPYTERM_CAPTURE_ACTIVE" ]; then
    export __COPYTERM_CAPTURE_ACTIVE=1
    exec > >(tee -a "$__copyterm_buf_file") 2>&1
fi

# Clear command interceptor to establish Capture Epoch boundary
clear() {
    __copyterm_epoch=$(( __copyterm_epoch + 1 ))
    local token="CPT_EPOCH_BOUND_${COPYTERM_SESSION_ID}_${__copyterm_epoch}"
    local ts=$(date +%s%3N 2>/dev/null || date +%s)
    printf '{"session_id":"%s","epoch_id":%d,"clear_count":%d,"last_clear_timestamp_ms":%s,"latest_boundary_token":"%s","clear_command":"clear"}\n' \
        "$COPYTERM_SESSION_ID" "$__copyterm_epoch" "$__copyterm_epoch" "$ts" "$token" > "$__copyterm_epoch_file" 2>/dev/null
    printf "\n%s\n" "$token" >> "$__copyterm_buf_file" 2>/dev/null
    command clear "$@"
}

# Resolve CopyTerm Executable / Python Core dynamically (CWD-Independent)
__copyterm_bin=""
__copyterm_py=""

# 1. Check user installation directory ~/.copyterm/bin
if [ -f "$__copyterm_data_dir/bin/cpt" ]; then
    __copyterm_bin="$__copyterm_data_dir/bin/cpt"
elif [ -f "$__copyterm_data_dir/bin/cpt.exe" ]; then
    __copyterm_bin="$__copyterm_data_dir/bin/cpt.exe"
fi
if [ -f "$__copyterm_data_dir/bin/copyterm.py" ]; then
    __copyterm_py="$__copyterm_data_dir/bin/copyterm.py"
fi

# 2. Check location relative to this script's physical path
if [ -z "$__copyterm_bin" ] && [ -z "$__copyterm_py" ] && [ -n "${BASH_SOURCE[0]}" ]; then
    _script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
    if [ -f "$_script_dir/../../src/copyterm.py" ]; then
        __copyterm_py="$_script_dir/../../src/copyterm.py"
    fi
    if [ -f "$_script_dir/../../cpt.exe" ]; then
        __copyterm_bin="$_script_dir/../../cpt.exe"
    elif [ -f "$_script_dir/../../copyterm.exe" ]; then
        __copyterm_bin="$_script_dir/../../copyterm.exe"
    elif [ -f "$_script_dir/../../copyterm" ]; then
        __copyterm_bin="$_script_dir/../../copyterm"
    fi
fi

cpt() {
    if [ -n "$__copyterm_py" ] && [ -f "$__copyterm_py" ]; then
        python3 "$__copyterm_py" "$@" 2>/dev/null || python "$__copyterm_py" "$@"
    elif [ -n "$__copyterm_bin" ] && [ -f "$__copyterm_bin" ]; then
        "$__copyterm_bin" "$@"
    elif command -v cpt >/dev/null 2>&1; then
        command cpt "$@"
    elif command -v copyterm >/dev/null 2>&1; then
        command copyterm "$@"
    else
        python3 -m copyterm "$@" 2>/dev/null || echo "cpt: command not found" >&2
    fi
}

copyterm() {
    cpt "$@"
}
