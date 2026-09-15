# ==============================================================================
# COPYTERM — PowerShell Integration Script
# Compatible with Windows PowerShell 5.1 and PowerShell Core 7+
# ==============================================================================

# 1. Initialize Unique Per-Session ID
if (-not $env:COPYTERM_SESSION_ID) {
    $ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $rnd = [System.Guid]::NewGuid().ToString("N").Substring(0, 6)
    $env:COPYTERM_SESSION_ID = "sess_${ts}_${PID}_${rnd}"
}

# 2. Configure Session Buffer Paths
$global:__copyterm_data_dir = if ($env:COPYTERM_DATA_DIR) { $env:COPYTERM_DATA_DIR } else { [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm") }
$global:__copyterm_session_dir = [System.IO.Path]::Combine($global:__copyterm_data_dir, "sessions")
$null = [System.IO.Directory]::CreateDirectory($global:__copyterm_session_dir)

$global:__copyterm_buf_file = [System.IO.Path]::Combine($global:__copyterm_session_dir, "$($env:COPYTERM_SESSION_ID).buf")
$global:__copyterm_meta_file = [System.IO.Path]::Combine($global:__copyterm_session_dir, "$($env:COPYTERM_SESSION_ID).meta")

# 3. Write Session Metadata
$metaContent = @"
session_id=$($env:COPYTERM_SESSION_ID)
shell_name=powershell
pid=$PID
ppid=$((Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction SilentlyContinue).ParentProcessId)
cwd=$((Get-Location).Path)
start_time_ms=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
last_active_time_ms=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
backend=shell_integration
"@
try {
    [System.IO.File]::WriteAllText($global:__copyterm_meta_file, $metaContent)
} catch {}

# 4. Command Recording Function
function global:__copyterm_record_command_internal {
    param([string]$cmd)
    if ([string]::IsNullOrWhiteSpace($cmd)) { return }
    $ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $cwd = (Get-Location).Path
    $record = "`n`e]133;C;cmd=$cmd;cwd=$cwd;ts=$ts`a`n`$ $cmd`n"
    try {
        [System.IO.File]::AppendAllText($global:__copyterm_buf_file, $record, [System.Text.Encoding]::UTF8)
    } catch {}
}

# 5. Hook the Prompt Function
if (Test-Path Function:\prompt) {
    $global:__copyterm_prev_prompt = $Function:prompt
} else {
    $global:__copyterm_prev_prompt = { "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) " }
}

$global:__copyterm_last_hist_id = -1

function global:prompt {
    try {
        $lastHist = Get-History -Count 1 -ErrorAction SilentlyContinue
        if ($lastHist -and ($global:__copyterm_last_hist_id -ne $lastHist.Id)) {
            $global:__copyterm_last_hist_id = $lastHist.Id
            global:__copyterm_record_command_internal $lastHist.CommandLine
        }
    } catch {}
    
    # Execute original prompt
    & $global:__copyterm_prev_prompt
}
