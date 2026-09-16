# ==============================================================================
# COPYTERM — PowerShell Integration Script
# Canonical Short Command: cpt (Alias: copyterm)
# Clear establishes a Capture Epoch boundary
# CWD-Independent Architecture: Works from any working directory
# Compatible with Windows PowerShell 5.1 and PowerShell Core 7+
# ==============================================================================

# 1. Initialize Unique Per-Session ID
if (-not $env:COPYTERM_SESSION_ID) {
    $ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    $rnd = [System.Guid]::NewGuid().ToString("N").Substring(0, 6)
    $env:COPYTERM_SESSION_ID = "sess_${ts}_${PID}_${rnd}"
}

# 2. Configure Persistent Session Storage in User Home (~/.copyterm)
$global:__copyterm_epoch = 0
$global:__copyterm_data_dir = if ($env:COPYTERM_DATA_DIR) { $env:COPYTERM_DATA_DIR } else { [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm") }
$global:__copyterm_session_dir = [System.IO.Path]::Combine($global:__copyterm_data_dir, "sessions")
try {
    $null = [System.IO.Directory]::CreateDirectory($global:__copyterm_session_dir)
} catch {}

$global:__copyterm_buf_file = [System.IO.Path]::Combine($global:__copyterm_session_dir, "$($env:COPYTERM_SESSION_ID).buf")
$global:__copyterm_meta_file = [System.IO.Path]::Combine($global:__copyterm_session_dir, "$($env:COPYTERM_SESSION_ID).meta")
$global:__copyterm_epoch_file = [System.IO.Path]::Combine($global:__copyterm_session_dir, "$($env:COPYTERM_SESSION_ID).epoch")

# 3. Write Initial Session Metadata & Epoch State
$metaContent = @"
session_id=$($env:COPYTERM_SESSION_ID)
shell_name=powershell
pid=$PID
ppid=$((Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction SilentlyContinue).ParentProcessId)
start_time_ms=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
last_active_time_ms=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
backend=shell_integration
"@
try {
    [System.IO.File]::WriteAllText($global:__copyterm_meta_file, $metaContent)
} catch {}

$initialEpochContent = @"
{"session_id":"$($env:COPYTERM_SESSION_ID)","epoch_id":0,"clear_count":0,"line_offset":0,"byte_offset":0,"last_clear_timestamp_ms":0,"latest_boundary_token":""}
"@
try {
    [System.IO.File]::WriteAllText($global:__copyterm_epoch_file, $initialEpochContent)
} catch {}

# 4. Start Full-Session Transcript (Fallback Stream Buffer)
try {
    if ($PSVersionTable.PSEdition -eq "Core") {
        Start-Transcript -Path $global:__copyterm_buf_file -Append -Force -UseMinimalHeader -ErrorAction SilentlyContinue | Out-Null
    } else {
        Start-Transcript -Path $global:__copyterm_buf_file -Append -Force -ErrorAction SilentlyContinue | Out-Null
    }
} catch {}

# 5. Intercept Clear Commands to Establish Capture Epoch Boundary
function global:Clear-Host {
    [CmdletBinding()]
    param()
    
    $global:__copyterm_epoch = [int]$global:__copyterm_epoch + 1
    $ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
    
    # Safely obtain current byte offset and line offset from .buf without exclusive locking
    $byteOffset = [long]0
    $lineOffset = [long]0
    try {
        if (Test-Path -LiteralPath $global:__copyterm_buf_file) {
            $fi = New-Object System.IO.FileInfo($global:__copyterm_buf_file)
            if ($fi.Exists) {
                $byteOffset = $fi.Length
            }
            # Count lines using non-exclusive Read + ReadWrite sharing
            $fs = New-Object System.IO.FileStream($global:__copyterm_buf_file, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
            try {
                $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::UTF8)
                try {
                    $cnt = 0
                    while ($null -ne ($sr.ReadLine())) {
                        $cnt++
                    }
                    $lineOffset = $cnt
                } finally {
                    $sr.Close()
                }
            } finally {
                $fs.Close()
            }
        }
    } catch {}

    $epochJson = @"
{"session_id":"$($env:COPYTERM_SESSION_ID)","epoch_id":$($global:__copyterm_epoch),"clear_count":$($global:__copyterm_epoch),"byte_offset":$byteOffset,"line_offset":$lineOffset,"last_clear_timestamp_ms":$ts,"latest_boundary_token":"","clear_command":"Clear-Host"}
"@
    # Safe atomic update to dedicated .epoch metadata file
    try {
        $tempEpoch = "$($global:__copyterm_epoch_file).$([System.Guid]::NewGuid().ToString('N')).tmp"
        [System.IO.File]::WriteAllText($tempEpoch, $epochJson, [System.Text.Encoding]::UTF8)
        if ([System.IO.File]::Exists($global:__copyterm_epoch_file)) {
            [System.IO.File]::Delete($global:__copyterm_epoch_file)
        }
        [System.IO.File]::Move($tempEpoch, $global:__copyterm_epoch_file)
    } catch {
        try {
            [System.IO.File]::WriteAllText($global:__copyterm_epoch_file, $epochJson, [System.Text.Encoding]::UTF8)
        } catch {}
    }

    # Perform native terminal screen clearing
    try {
        [System.Console]::Clear()
    } catch {
        try {
            $host.UI.RawUI.CursorPosition = New-Object System.Management.Automation.Host.Coordinates 0, 0
            $host.UI.RawUI.FlushInputBuffer()
        } catch {}
    }
}

# Ensure clear and cls aliases route to Clear-Host
Set-Alias -Name clear -Value Clear-Host -Scope Global -Option AllScope -Force -ErrorAction SilentlyContinue
Set-Alias -Name cls -Value Clear-Host -Scope Global -Option AllScope -Force -ErrorAction SilentlyContinue

# 6. Dynamic Executable Resolution (CWD-Independent)
$global:__copyterm_bin = $null
$global:__copyterm_py = $null

# Option A: Check user installation directory ~/.copyterm/bin
try {
    $userBinDir = [System.IO.Path]::Combine($global:__copyterm_data_dir, "bin")
    $cptExePath = [System.IO.Path]::Combine($userBinDir, "cpt.exe")
    $cptAltPath = [System.IO.Path]::Combine($userBinDir, "copyterm.exe")
    $cptPyPath  = [System.IO.Path]::Combine($userBinDir, "copyterm.py")

    if (Test-Path $cptExePath -ErrorAction SilentlyContinue) {
        $global:__copyterm_bin = $cptExePath
    } elseif (Test-Path $cptAltPath -ErrorAction SilentlyContinue) {
        $global:__copyterm_bin = $cptAltPath
    }
    if (Test-Path $cptPyPath -ErrorAction SilentlyContinue) {
        $global:__copyterm_py = $cptPyPath
    }
} catch {}

# Option B: Check location relative to this script's physical path ($PSScriptRoot)
if (-not $global:__copyterm_bin -and -not $global:__copyterm_py -and $PSScriptRoot) {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..") -ErrorAction SilentlyContinue).Path
    if ($repoRoot) {
        if (Test-Path (Join-Path $repoRoot "src\copyterm.py")) {
            $global:__copyterm_py = Join-Path $repoRoot "src\copyterm.py"
        }
        if (Test-Path (Join-Path $repoRoot "cpt.exe")) {
            $global:__copyterm_bin = Join-Path $repoRoot "cpt.exe"
        } elseif (Test-Path (Join-Path $repoRoot "copyterm.exe")) {
            $global:__copyterm_bin = Join-Path $repoRoot "copyterm.exe"
        }
    }
}

# Option C: Check PATH for installed binary
if (-not $global:__copyterm_bin) {
    $pathCmd = Get-Command "cpt.exe" -ErrorAction SilentlyContinue
    if (-not $pathCmd) { $pathCmd = Get-Command "copyterm.exe" -ErrorAction SilentlyContinue }
    if ($pathCmd) { $global:__copyterm_bin = $pathCmd.Source }
}

# 7. Define Canonical cpt Command & copyterm Alias
function global:cpt {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ArgsList
    )
    if ($global:__copyterm_py -and (Test-Path $global:__copyterm_py)) {
        python $global:__copyterm_py @ArgsList
    } elseif ($global:__copyterm_bin -and (Test-Path $global:__copyterm_bin)) {
        & $global:__copyterm_bin @ArgsList
    } else {
        # Fallback to PATH resolution
        try {
            cpt.exe @ArgsList
        } catch {
            copyterm.exe @ArgsList
        }
    }
}

function global:copyterm {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ArgsList
    )
    cpt @ArgsList
}
