# ==============================================================================
# COPYTERM — 30 Concurrent Terminal Session Isolation Integration Test
# ==============================================================================
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   COPYTERM 30 CONCURRENT TERMINAL ISOLATION INTEGRATION TEST" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$copytermBin = Join-Path (Get-Location).Path "copyterm.exe"
if (-not (Test-Path $copytermBin)) {
    Write-Error "copyterm.exe not found. Build first with scripts/build.ps1"
}

$numTerminals = 30
$sessions = @()
$testDir = [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm", "sessions")
$null = [System.IO.Directory]::CreateDirectory($testDir)

Write-Host "Spawning $numTerminals simulated independent terminals..." -ForegroundColor Yellow

for ($i = 1; $i -le $numTerminals; $i++) {
    $sessId = "sess_integration_test_term_$($i.ToString('00'))_$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())"
    $bufFile = [System.IO.Path]::Combine($testDir, "$sessId.buf")
    $metaFile = [System.IO.Path]::Combine($testDir, "$sessId.meta")

    # Write metadata
    $metaContent = "session_id=$sessId`nshell_name=powershell`npid=$($i * 1000 + 123)`ncwd=C:\projects\app_$i`nterminal_name=Windows Terminal (Tab $i)`nstart_time_ms=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())`nlast_active_time_ms=$([DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())`nbackend=shell_integration`n"
    [System.IO.File]::WriteAllText($metaFile, $metaContent)

    # Write distinct terminal content with exact unique tokens
    $token = "TOKEN_TERM_$($i.ToString('00'))_EXACT"
    $content = "`e]133;C;cmd=cd C:\projects\app_$i;cwd=C:\projects\app_$i;ts=170000000$i`a`n`$ cd C:\projects\app_$i`n`e]133;C;cmd=make;cwd=C:\projects\app_$i;ts=170000001$i`a`n`$ make`n[TERM_$i] Compiling module $i...`n[TERM_$i] Linking binary app_$i.exe`n[TERM_$i] $token`n`e]133;C;cmd=./test.sh;cwd=C:\projects\app_$i;ts=170000002$i`a`n`$ ./test.sh`nAll tests passed for project $i.`n"
    [System.IO.File]::WriteAllText($bufFile, $content)

    $sessions += [PSCustomObject]@{
        Index = $i
        SessionId = $sessId
        Token = $token
        BufFile = $bufFile
        MetaFile = $metaFile
    }
}

Write-Host "Created $numTerminals isolated sessions. Verifying isolation across all sessions...`n" -ForegroundColor Yellow

$failures = 0

for ($i = 1; $i -le $numTerminals; $i++) {
    $current = $sessions[$i - 1]
    
    # Execute copyterm with --stdout --session-id to retrieve captured content as string
    $output = (& $copytermBin --stdout --session-id $current.SessionId | Out-String)

    # 1. Verify current session has its own unique token
    if ($output -notmatch "\b$($current.Token)\b") {
        Write-Host "[FAIL] Terminal $i is missing its expected token ($($current.Token))" -ForegroundColor Red
        $failures++
        continue
    }

    # 2. Verify current session does NOT contain any token from any other terminal
    $leakDetected = $false
    for ($j = 1; $j -le $numTerminals; $j++) {
        if ($i -eq $j) { continue }
        $otherToken = "TOKEN_TERM_$($j.ToString('00'))_EXACT"
        if ($output -match "\b$otherToken\b") {
            Write-Host "[FAIL] Terminal $i cross-contaminated with Terminal $j token ($otherToken)!" -ForegroundColor Red
            $leakDetected = $true
            $failures++
            break
        }
    }

    if (-not $leakDetected) {
        Write-Host "  [OK] Terminal $i ($($current.SessionId.Substring(0, 32))...) - 100% Isolated" -ForegroundColor Green
    }
}

# Cleanup test sessions
foreach ($s in $sessions) {
    if (Test-Path $s.BufFile) { Remove-Item $s.BufFile -Force }
    if (Test-Path $s.MetaFile) { Remove-Item $s.MetaFile -Force }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
if ($failures -eq 0) {
    Write-Host "SUCCESS: All $numTerminals terminals verified 100% isolated with ZERO cross-contamination!" -ForegroundColor Green
} else {
    Write-Host "FAILURE: Detected $failures isolation failure(s)!" -ForegroundColor Red
    exit 1
}
Write-Host "============================================================`n" -ForegroundColor Cyan
