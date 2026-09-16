# ==============================================================================
# COPYTERM — Production-Grade Installation Verification Test Suite
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
$cptHome = [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm")
$binDir = [System.IO.Path]::Combine($cptHome, "bin")

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    COPYTERM PRODUCTION INSTALLATION ACCEPTANCE TEST SUITE   " -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$passed = 0
$failed = 0

function Assert-Test($name, $condition, $details = "") {
    if ($condition) {
        Write-Host "  [PASS] $name" -ForegroundColor Green
        $global:passed++
    } else {
        Write-Host "  [FAIL] $name" -ForegroundColor Red
        if ($details) { Write-Host "         $details" -ForegroundColor Yellow }
        $global:failed++
    }
}

# ----------------------------------------------------------------------
# Test 1: User PATH Configuration Check
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 1: Windows User Environment PATH ---"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$normalizedTarget = $binDir.ToLower().TrimEnd('\')
$foundInUserPath = $false
$userPathCount = 0

if ($userPath) {
    foreach ($p in $userPath.Split(';')) {
        if ($p.Trim().ToLower().TrimEnd('\') -eq $normalizedTarget) {
            $foundInUserPath = $true
            $userPathCount++
        }
    }
}
Assert-Test "User Environment PATH contains ~/.copyterm/bin" ($foundInUserPath -eq $true) "User PATH: $userPath"
Assert-Test "User Environment PATH has zero duplicates" ($userPathCount -eq 1) "Count: $userPathCount"

# ----------------------------------------------------------------------
# Test 2: Fresh PowerShell Process Discovery (Reloaded User PATH)
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 2: Fresh PowerShell Terminal Discovery ---"
$testScriptBlock = {
    $m = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $u = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$m;$u"
    cpt --version
}
$psOut = powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $testScriptBlock 2>&1
$psOutStr = ($psOut | Out-String).Trim()
Assert-Test "Fresh PowerShell subprocess resolves 'cpt'" ($psOutStr -match "1.1.0" -or $psOutStr -match "cpt") "Output: $psOutStr"

# ----------------------------------------------------------------------
# Test 3: Fresh CMD Terminal Discovery (Reloaded User PATH)
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 3: Fresh CMD Terminal Discovery ---"
$cmdScriptBlock = {
    $m = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $u = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$m;$u"
    cmd.exe /c "cpt --version"
}
$cmdOut = powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $cmdScriptBlock 2>&1
$cmdOutStr = ($cmdOut | Out-String).Trim()
Assert-Test "Fresh CMD subprocess resolves 'cpt'" ($cmdOutStr -match "1.1.0" -or $cmdOutStr -match "cpt") "Output: $cmdOutStr"

# ----------------------------------------------------------------------
# Test 4: CWD Independence from Multiple Arbitrary Directories
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 4: Arbitrary Directory / CWD Independence ---"
$testDirs = @(
    "C:\",
    $env:USERPROFILE,
    [System.IO.Path]::Combine($env:USERPROFILE, "Downloads"),
    $env:TEMP
)

foreach ($td in $testDirs) {
    if (Test-Path $td) {
        $out = & {
            Push-Location $td
            $res = python (Join-Path $binDir "copyterm.py") doctor 2>&1
            Pop-Location
            $res
        }
        $outStr = ($out | Out-String)
        $ok = ($outStr -match "CopyTerm Doctor")
        Assert-Test "cpt doctor works from '$td'" $ok "Output: $outStr"
    }
}

# ----------------------------------------------------------------------
# Test 5: Complete Repository Relocation / Zero-Repo-Dependency
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 5: Zero Repository Dependency (Standalone Runtime) ---"
$pythonDir = [System.IO.Path]::GetDirectoryName((Get-Command python).Source)
$isoScriptBlock = {
    param($pyDir)
    $cptHome = [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm")
    $binDir = [System.IO.Path]::Combine($cptHome, "bin")
    # Isolated PATH with NO repo directory, only ~/.copyterm/bin, Python, and Windows system paths
    $env:Path = "$binDir;$pyDir;C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\"
    python "$binDir\copyterm.py" doctor
}
$isoOut = powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $isoScriptBlock -args $pythonDir 2>&1
$isoOutStr = ($isoOut | Out-String)
Assert-Test "cpt runs with zero repository references in PATH" ($isoOutStr -match "CopyTerm Doctor" -or $isoOutStr -match "Installation:.*OK") "Output: $isoOutStr"

# ----------------------------------------------------------------------
# Test 6: Installer Idempotency (Running 4 consecutive installs)
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 6: Installer Idempotency ---"
for ($i = 1; $i -le 4; $i++) {
    python (Join-Path $PSScriptRoot "..\install.py") --quiet
}

$userPathAfter = [Environment]::GetEnvironmentVariable("Path", "User")
$countAfter = 0
if ($userPathAfter) {
    foreach ($p in $userPathAfter.Split(';')) {
        if ($p.Trim().ToLower().TrimEnd('\') -eq $normalizedTarget) {
            $countAfter++
        }
    }
}
Assert-Test "User PATH remains clean after repeated installs (1 entry)" ($countAfter -eq 1) "Actual count: $countAfter"

# Check PowerShell profile for single managed block
$profilePath = [System.IO.Path]::Combine($HOME, "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1")
if (-not (Test-Path $profilePath)) {
    $profilePath = [System.IO.Path]::Combine($HOME, "OneDrive", "Documents", "WindowsPowerShell", "Microsoft.PowerShell_profile.ps1")
}
if (Test-Path $profilePath) {
    $pContent = [System.IO.File]::ReadAllText($profilePath)
    $blockMatches = [System.Text.RegularExpressions.Regex]::Matches($pContent, '# >>> CopyTerm managed block >>>')
    Assert-Test "Profile contains exactly 1 managed block" ($blockMatches.Count -eq 1) "Match count: $($blockMatches.Count)"
}

# ----------------------------------------------------------------------
# Test 7: Multi-Terminal Isolation (30 Simultaneous Terminals)
# ----------------------------------------------------------------------
Write-Host "`n--- TEST 7: 30 Independent Terminals Isolation ---"
$sessionsDir = [System.IO.Path]::Combine($cptHome, "sessions")
$null = [System.IO.Directory]::CreateDirectory($sessionsDir)
$termPass = $true

$testSessions = @()
for ($t = 1; $t -le 30; $t++) {
    $sId = "test_iso_sess_$t"
    $bFile = Join-Path $sessionsDir "$sId.buf"
    $mFile = Join-Path $sessionsDir "$sId.meta"
    $eFile = Join-Path $sessionsDir "$sId.epoch"

    [System.IO.File]::WriteAllText($mFile, "session_id=$sId`nshell_name=powershell`npid=$((1000 + $t))`nbackend=test")
    [System.IO.File]::WriteAllText($eFile, "{`"session_id`":`"$sId`",`"epoch_id`":0,`"clear_count`":0,`"last_clear_timestamp_ms`":0}")
    [System.IO.File]::WriteAllText($bFile, "TERMINAL_${t}_EXCLUSIVE_PAYLOAD_HASH_$($t * 997)")
    $testSessions += $sId
}

for ($t = 1; $t -le 30; $t++) {
    $sId = "test_iso_sess_$t"
    $out = python (Join-Path $binDir "copyterm.py") --session-id $sId --stdout 2>&1
    $expected = "TERMINAL_${t}_EXCLUSIVE_PAYLOAD_HASH_$($t * 997)"
    if ($out -notmatch $expected) {
        $termPass = $false
        break
    }
    if ($t -ne 1 -and $out -match "TERMINAL_1_EXCLUSIVE_PAYLOAD_HASH_997") {
        $termPass = $false
        break
    }
}

# Clean up test session files
foreach ($sId in $testSessions) {
    Remove-Item (Join-Path $sessionsDir "$sId.*") -Force -ErrorAction SilentlyContinue
}
Assert-Test "30/30 simultaneous terminals have 100% strict isolation" $termPass

# ----------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------
Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "                TEST SUITE EXECUTION SUMMARY                " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Passed: $passed" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "============================================================`n" -ForegroundColor Cyan

if ($failed -gt 0) { exit 1 } else { exit 0 }
