# ==============================================================================
# COPYTERM — Windows One-Click Bootstrap Installer
# Canonical Command: cpt (Alias: copyterm)
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$repoRoot = $PSScriptRoot
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }

# If Python is available, execute the python installer engine
$pythonCmd = Get-Command "python.exe" -ErrorAction SilentlyContinue
if (-not $pythonCmd) { $pythonCmd = Get-Command "python" -ErrorAction SilentlyContinue }

if ($pythonCmd -and (Test-Path (Join-Path $repoRoot "install.py"))) {
    $pyArgs = @((Join-Path $repoRoot "install.py"))
    if ($Uninstall) { $pyArgs += "--uninstall" }
    if ($Quiet) { $pyArgs += "--quiet" }
    & $pythonCmd.Source @pyArgs
    exit $LASTEXITCODE
}

# Native PowerShell Fallback Installer
$cptHome = if ($env:USERPROFILE) { [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm") } else { [System.IO.Path]::Combine($HOME, ".copyterm") }
$binDir = [System.IO.Path]::Combine($cptHome, "bin")
$integrationsDir = [System.IO.Path]::Combine($cptHome, "integrations")
$sessionsDir = [System.IO.Path]::Combine($cptHome, "sessions")
$logsDir = [System.IO.Path]::Combine($cptHome, "logs")
$servicesDir = [System.IO.Path]::Combine($cptHome, "services")

function Write-Step($stepNum, $stepName, $status) {
    if (-not $Quiet) {
        $prefix = "[$stepNum/7] $stepName"
        $pad = "." * [Math]::Max(2, (38 - $prefix.Length))
        Write-Host "$prefix $pad $status"
    }
}

if ($Uninstall) {
    if (-not $Quiet) {
        Write-Host "`n==================================================" -ForegroundColor Cyan
        Write-Host "             CopyTerm Uninstaller                 " -ForegroundColor Cyan
        Write-Host "==================================================`n" -ForegroundColor Cyan
    }

    # 1. Remove from User PATH
    try {
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($userPath) {
            $parts = $userPath.Split(';') | Where-Object { $_.Trim() -ne "" -and $_.Trim().ToLower().TrimEnd('\') -ne $binDir.ToLower().TrimEnd('\') }
            $newPath = $parts -join ";"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        }
        Write-Host "[1/4] Removing from PATH ............. OK"
    } catch {
        Write-Host "[1/4] Removing from PATH ............. WARN"
    }

    # 2. Remove profile hooks
    $profiles = @(
        [System.IO.Path]::Combine($HOME, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        [System.IO.Path]::Combine($HOME, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
        [System.IO.Path]::Combine($HOME, "OneDrive", "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        [System.IO.Path]::Combine($HOME, "OneDrive", "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1")
    )
    foreach ($p in $profiles) {
        if (Test-Path $p) {
            try {
                $content = [System.IO.File]::ReadAllText($p)
                $pattern = '(?s)\r?\n?# >>> CopyTerm managed block >>>.*?# <<< CopyTerm managed block <<<\r?\n?'
                $newContent = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, "`n").Trim() + "`n"
                [System.IO.File]::WriteAllText($p, $newContent)
            } catch {}
        }
    # Remove CMD AutoRun
    try {
        $regKey = "HKCU:\Software\Microsoft\Command Processor"
        if (Test-Path $regKey) {
            $currentAutoRun = (Get-ItemProperty -Path $regKey -Name "AutoRun" -ErrorAction SilentlyContinue).AutoRun
            if ($currentAutoRun -and $currentAutoRun -match "copyterm_init\.cmd") {
                $parts = $currentAutoRun.Split('&') | Where-Object { $_.Trim() -ne "" -and $_ -notmatch "copyterm_init\.cmd" }
                $newAutoRun = ($parts | ForEach-Object { $_.Trim() }) -join " & "
                if ($newAutoRun) {
                    Set-ItemProperty -Path $regKey -Name "AutoRun" -Value $newAutoRun -Type String -Force
                } else {
                    Remove-ItemProperty -Path $regKey -Name "AutoRun" -ErrorAction SilentlyContinue
                }
            }
        }
    } catch {}

    Write-Host "[2/4] Removing shell hooks ........... OK"

    # 3. Remove IDE extensions
    $agExt = [System.IO.Path]::Combine($HOME, ".antigravity-ide", "extensions", "copyterm.copyterm-terminal-bridge-1.0.0")
    if (Test-Path $agExt) { Remove-Item -Recurse -Force $agExt -ErrorAction SilentlyContinue }
    $vsExt = [System.IO.Path]::Combine($HOME, ".vscode", "extensions", "copyterm.copyterm-terminal-bridge-1.0.0")
    if (Test-Path $vsExt) { Remove-Item -Recurse -Force $vsExt -ErrorAction SilentlyContinue }
    Write-Host "[3/4] Removing IDE extension ......... OK"

    # 4. Remove binaries
    if (Test-Path $binDir) { Remove-Item -Recurse -Force $binDir -ErrorAction SilentlyContinue }
    if (Test-Path $integrationsDir) { Remove-Item -Recurse -Force $integrationsDir -ErrorAction SilentlyContinue }
    Write-Host "[4/4] Removing binaries .............. OK"

    Write-Host "`nCopyTerm uninstallation complete.`n" -ForegroundColor Green
    exit 0
}

# Detection
$osDisplay = "Windows"
$arch = if ([IntPtr]::Size -eq 8) { "x64" } else { "x86" }
$shellDisplay = if ($PSVersionTable.PSEdition -eq "Core") { "PowerShell Core" } else { "PowerShell" }
$termDisplay = if ($env:WT_SESSION) { "Windows Terminal" } elseif ($env:TERM_PROGRAM) { $env:TERM_PROGRAM } else { "Windows Console" }
$ideDisplay = if (Test-Path (Join-Path $HOME ".antigravity-ide")) { "Antigravity" } elseif (Test-Path (Join-Path $HOME ".vscode")) { "VS Code" } else { "Not detected" }

if (-not $Quiet) {
    Write-Host "`n==================================================" -ForegroundColor Cyan
    Write-Host "               CopyTerm Installer                 " -ForegroundColor Cyan
    Write-Host "==================================================`n" -ForegroundColor Cyan
    Write-Host "Detected OS       : $osDisplay"
    Write-Host "Architecture      : $arch"
    Write-Host "Shell             : $shellDisplay"
    Write-Host "Terminal          : $termDisplay"
    Write-Host "IDE               : $ideDisplay"
    Write-Host ""
}

# [1/7] Installing binary
try {
    $null = [System.IO.Directory]::CreateDirectory($binDir)
    $null = [System.IO.Directory]::CreateDirectory($integrationsDir)
    $null = [System.IO.Directory]::CreateDirectory($sessionsDir)
    $null = [System.IO.Directory]::CreateDirectory($logsDir)
    $null = [System.IO.Directory]::CreateDirectory($servicesDir)

    # Copy copyterm.py
    if (Test-Path (Join-Path $repoRoot "src\copyterm.py")) {
        Copy-Item (Join-Path $repoRoot "src\copyterm.py") (Join-Path $binDir "copyterm.py") -Force
    }

    # Copy binaries
    foreach ($binName in @("cpt.exe", "copyterm.exe", "copyterm_bin.exe", "copyterm_tests.exe")) {
        $srcBin = Join-Path $repoRoot $binName
        if (Test-Path $srcBin) {
            Copy-Item $srcBin (Join-Path $binDir $binName) -Force
        }
    }

    # Copy integrations
    $srcIntegrations = Join-Path $repoRoot "integrations"
    if (Test-Path $srcIntegrations) {
        Copy-Item -Path "$srcIntegrations\*" -Destination $integrationsDir -Recurse -Force
    }

    # Copy CMD wrappers
    $cmdSrc = Join-Path $srcIntegrations "cmd"
    if (Test-Path $cmdSrc) {
        Copy-Item -Path "$cmdSrc\*.cmd" -Destination $binDir -Force -ErrorAction SilentlyContinue
    }

    Write-Step 1 "Installing binary" "OK"
} catch {
    Write-Step 1 "Installing binary" "FAIL"
    Write-Error $_
}

# [2/7] Configuring PATH
try {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $normalizedTarget = $binDir.ToLower().TrimEnd('\')
    $alreadyInPath = $false

    if ($userPath) {
        $parts = $userPath.Split(';')
        foreach ($p in $parts) {
            if ($p.Trim().ToLower().TrimEnd('\') -eq $normalizedTarget) {
                $alreadyInPath = $true
                break
            }
        }
    }

    if (-not $alreadyInPath) {
        $newPath = if ($userPath) { "$userPath;$binDir" } else { $binDir }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }

    # Update current process PATH
    if ($env:Path -notlike "*$binDir*") {
        $env:Path = "$binDir;$env:Path"
    }

    Write-Step 2 "Configuring PATH" "OK"
} catch {
    Write-Step 2 "Configuring PATH" "FAIL"
}

# [3/7] Installing PowerShell hook
try {
    $psHookSnippet = @"
# >>> CopyTerm managed block >>>
`$__copyterm_ps1 = [System.IO.Path]::Combine(`$env:USERPROFILE, ".copyterm", "integrations", "powershell", "copyterm.ps1")
if (Test-Path `$__copyterm_ps1) { . `$__copyterm_ps1 }
# <<< CopyTerm managed block <<<
"@

    $profiles = @(
        [System.IO.Path]::Combine($HOME, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        [System.IO.Path]::Combine($HOME, "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1"),
        [System.IO.Path]::Combine($HOME, "OneDrive", "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1"),
        [System.IO.Path]::Combine($HOME, "OneDrive", "Documents", "PowerShell", "Microsoft.PowerShell_profile.ps1")
    )

    foreach ($profPath in $profiles) {
        $profDir = [System.IO.Path]::GetDirectoryName($profPath)
        if (Test-Path $profDir -or $profDir.Contains("Documents")) {
            [System.IO.Directory]::CreateDirectory($profDir) | Out-Null
            $content = if (Test-Path $profPath) { [System.IO.File]::ReadAllText($profPath) } else { "" }
            
            $pattern = '(?s)\r?\n?# >>> CopyTerm.*?# <<< CopyTerm.*?\r?\n?'
            if ([System.Text.RegularExpressions.Regex]::IsMatch($content, $pattern)) {
                $newContent = [System.Text.RegularExpressions.Regex]::Replace($content, $pattern, "`n$psHookSnippet`n")
                [System.IO.File]::WriteAllText($profPath, $newContent)
            } else {
                $appendContent = if ($content -and -not $content.EndsWith("`n")) { "`n`n$psHookSnippet`n" } else { "`n$psHookSnippet`n" }
                [System.IO.File]::AppendAllText($profPath, $appendContent)
            }
        }
    }

    # CMD AutoRun is intentionally omitted for safety (CMD commands run directly via PATH)
    Write-Step 3 "Installing shell hooks" "OK"
} catch {
    Write-Step 3 "Installing shell hooks" "FAIL"
}

# [4/7] Configuring IDE bridge
try {
    $srcExt = Join-Path $repoRoot "extensions\copyterm-terminal-bridge"
    if (Test-Path $srcExt) {
        $agExt = [System.IO.Path]::Combine($HOME, ".antigravity-ide", "extensions", "copyterm.copyterm-terminal-bridge-1.0.0")
        $null = [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($agExt))
        if (Test-Path $agExt) { Remove-Item -Recurse -Force $agExt -ErrorAction SilentlyContinue }
        Copy-Item -Path $srcExt -Destination $agExt -Recurse -Force -ErrorAction SilentlyContinue

        $vsExt = [System.IO.Path]::Combine($HOME, ".vscode", "extensions", "copyterm.copyterm-terminal-bridge-1.0.0")
        $null = [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($vsExt))
        if (Test-Path $vsExt) { Remove-Item -Recurse -Force $vsExt -ErrorAction SilentlyContinue }
        Copy-Item -Path $srcExt -Destination $vsExt -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Step 4 "Configuring IDE bridge" "OK"
} catch {
    Write-Step 4 "Configuring IDE bridge" "WARN"
}

# [5/7] Configuring runtime state
try {
    $cfgPath = Join-Path $cptHome "config.json"
    if (-not (Test-Path $cfgPath)) {
        $cfgJson = '{"version":"1.1.0","default_clean":true,"capture_tier_order":["ide_bridge","tmux","transcript"],"max_history_lines":50000}'
        [System.IO.File]::WriteAllText($cfgPath, $cfgJson)
    }
    Write-Step 5 "Configuring runtime state" "OK"
} catch {
    Write-Step 5 "Configuring runtime state" "FAIL"
}

# [6/7] Configuring services
Write-Step 6 "Configuring services" "N/A"

# [7/7] Running verification
$verPass = (Test-Path (Join-Path $binDir "cpt.exe")) -or (Test-Path (Join-Path $binDir "copyterm.py"))
Write-Step 7 "Running verification" $(if ($verPass) { "OK" } else { "FAIL" })

if (-not $Quiet) {
    Write-Host "`n--------------------------------------------------" -ForegroundColor Green
    Write-Host " CopyTerm installation successful." -ForegroundColor Green
    Write-Host "--------------------------------------------------" -ForegroundColor Green
    Write-Host "`nCommand:"
    Write-Host "    cpt  (alias: copyterm)" -ForegroundColor Cyan
    Write-Host "`nRuntime:"
    Write-Host "    $cptHome"
    Write-Host "`nOpen a new terminal before using cpt.`n" -ForegroundColor Yellow
}
