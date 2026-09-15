#!/usr/bin/env zsh
# ==============================================================================
# COPYTERM — Zsh Integration Script
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

cat <<EOF > "$__copyterm_meta_file" 2>/dev/null
session_id=$COPYTERM_SESSION_ID
shell_name=zsh
pid=$$
ppid=$PPID
cwd=$PWD
tty=$(tty 2>/dev/null || echo "unknown")
start_time_ms=$(date +%s%3N 2>/dev/null || date +%s)
last_active_time_ms=$(date +%s%3N 2>/dev/null || date +%s)
backend=shell_integration
EOF

__copyterm_preexec() {
    local cmd="$1"
    [ -z "$cmd" ] && return
    local ts=$(date +%s%3N 2>/dev/null || date +%s)
    printf "\n\033]133;C;cmd=%s;cwd=%s;ts=%s\007\n$ %s\n" "$cmd" "$PWD" "$ts" "$cmd" >> "$__copyterm_buf_file" 2>/dev/null
}

autoload -Uz add-zsh-hook 2>/dev/null
if (( $+functions[add-zsh-hook] )); then
    add-zsh-hook preexec __copyterm_preexec
fi
