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
try {
    $null = [System.IO.Directory]::CreateDirectory($global:__copyterm_session_dir)
} catch {}

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

# 4. Start Real Full-Session Transcript (Captures Commands + STDOUT + STDERR)
try {
    Start-Transcript -Path $global:__copyterm_buf_file -Append -Force -UseMinimalHeader -ErrorAction SilentlyContinue | Out-Null
} catch {
    try {
        Start-Transcript -Path $global:__copyterm_buf_file -Append -Force -ErrorAction SilentlyContinue | Out-Null
    } catch {}
}

# 5. Define copyterm Command Shortcut
function global:copyterm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ArgsList
    )
    $repoRoot = "C:\Users\satis\OneDrive\Desktop\Copyterm"
    $pyScript = Join-Path $repoRoot "src\copyterm.py"
    if (Test-Path $pyScript) {
        python $pyScript @ArgsList
    } else {
        & "$repoRoot\copyterm.exe" @ArgsList
    }
}
