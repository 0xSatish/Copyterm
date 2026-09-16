# ==============================================================================
# COPYTERM — End-to-End PowerShell Integration Test for cpt & Capture Epochs
# ==============================================================================
$ErrorActionPreference = "Stop"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$psIntegration = Join-Path $repoRoot "integrations\powershell\copyterm.ps1"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "     COPYTERM POWERSHELL E2E INTEGRATION TEST SUITE         " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Test 1: Source PowerShell Integration
Write-Host "`n[Test 1] Sourcing PowerShell integration..." -ForegroundColor Yellow
. $psIntegration

if ((Get-Command cpt -ErrorAction SilentlyContinue) -and (Get-Command copyterm -ErrorAction SilentlyContinue)) {
    Write-Host "  -> PASS: 'cpt' and 'copyterm' commands are defined in global scope" -ForegroundColor Green
} else {
    Write-Error "FAIL: 'cpt' or 'copyterm' function missing!"
}

# Test 2: Initial Epoch State
Write-Host "`n[Test 2] Verifying initial session & epoch..." -ForegroundColor Yellow
$epochFile = Join-Path $global:__copyterm_session_dir "$($env:COPYTERM_SESSION_ID).epoch"
if (Test-Path $epochFile) {
    $epochData = Get-Content $epochFile | ConvertFrom-Json
    if ($epochData.epoch_id -eq 0) {
        Write-Host "  -> PASS: Initial epoch_id is 0" -ForegroundColor Green
    } else {
        Write-Error "FAIL: Initial epoch_id is $($epochData.epoch_id), expected 0"
    }
} else {
    Write-Error "FAIL: Epoch file not created at $epochFile"
}

# Test 3: Clear-Host advances epoch
Write-Host "`n[Test 3] Testing Clear-Host / clear epoch increment..." -ForegroundColor Yellow
Clear-Host
$epochData = Get-Content $epochFile | ConvertFrom-Json
if ($epochData.epoch_id -eq 1) {
    Write-Host "  -> PASS: Clear-Host advanced epoch_id to 1" -ForegroundColor Green
} else {
    Write-Error "FAIL: epoch_id is $($epochData.epoch_id), expected 1"
}

# Test 4: cls alias advances epoch
cls
$epochData = Get-Content $epochFile | ConvertFrom-Json
if ($epochData.epoch_id -eq 2) {
    Write-Host "  -> PASS: cls alias advanced epoch_id to 2" -ForegroundColor Green
} else {
    Write-Error "FAIL: epoch_id is $($epochData.epoch_id), expected 2"
}

# Test 5: Output generation and cpt --stdout capture
Write-Host "`n[Test 5] Generating test payload in current epoch and capturing..." -ForegroundColor Yellow
Clear-Host # Epoch 3
1..100 | ForEach-Object { Write-Output "PS_EPOCH3_LINE_$($_)_" + ("X" * 60) }

$captureFile = Join-Path $env:TEMP "cpt_stdout_test.txt"
if (Test-Path $captureFile) { Remove-Item $captureFile -Force }

Start-Sleep -Milliseconds 200
Write-Host "DEBUG: session_id = $env:COPYTERM_SESSION_ID"
Write-Host "DEBUG: epoch_file = $(Get-Content $epochFile)"
Write-Host "DEBUG: buf_file length = $((Get-Item $global:__copyterm_buf_file).Length)"

cpt --session-id $env:COPYTERM_SESSION_ID --stdout > $captureFile
$capturedContent = Get-Content $captureFile -Raw

$allLinesPresent = $true
1..100 | ForEach-Object {
    if ($capturedContent -notmatch "PS_EPOCH3_LINE_$($_)_") {
        $allLinesPresent = $false
    }
}

if ($allLinesPresent) {
    Write-Host "  -> PASS: All 20 lines from Epoch 3 captured via cpt --stdout" -ForegroundColor Green
} else {
    Write-Host "  -> Captured sample:`n$capturedContent" -ForegroundColor Magenta
    Write-Error "FAIL: Captured content missing expected lines!"
}

# Test 6: Verify cpt doctor output
Write-Host "`n[Test 6] Verifying cpt doctor..." -ForegroundColor Yellow
$docOut = cpt doctor --session-id $env:COPYTERM_SESSION_ID | Out-String
if ($docOut -match "Command:\s+cpt" -and $docOut -match "Current Epoch:\s+3" -and $docOut -match "Boundary Tracking:\s+AVAILABLE") {
    Write-Host "  -> PASS: cpt doctor reports Command, Session, Current Epoch 3, and Boundary Tracking" -ForegroundColor Green
} else {
    Write-Host "Doctor output:`n$docOut" -ForegroundColor Magenta
    Write-Error "FAIL: cpt doctor output missing expected fields"
}

# Test 7: Multi-Terminal Runspace Isolation Test
Write-Host "`n[Test 7] Testing Multi-Terminal Session Isolation..." -ForegroundColor Yellow
$testIsoScript = {
    param($termName, $repoRoot)
    . (Join-Path $repoRoot "integrations\powershell\copyterm.ps1")
    
    # Pre-clear output
    Write-Output "OLD_${termName}_1" | Out-Default
    Write-Output "OLD_${termName}_2" | Out-Default
    Clear-Host
    # Post-clear output
    1..50 | ForEach-Object { Write-Output "NEW_${termName}_$_" | Out-Default }
    
    Start-Sleep -Milliseconds 200
    # Capture stdout
    $captured = cpt --stdout | Out-String
    return $captured
}

$resA = powershell -NoProfile -ExecutionPolicy Bypass -Command $testIsoScript -args "TERM_A", $repoRoot
$resB = powershell -NoProfile -ExecutionPolicy Bypass -Command $testIsoScript -args "TERM_B", $repoRoot

$aValid = ($resA -match "NEW_TERM_A_1") -and ($resA -match "NEW_TERM_A_50") -and ($resA -notmatch "OLD_TERM_A") -and ($resA -notmatch "TERM_B")
$bValid = ($resB -match "NEW_TERM_B_1") -and ($resB -match "NEW_TERM_B_50") -and ($resB -notmatch "OLD_TERM_B") -and ($resB -notmatch "TERM_A")

if ($aValid -and $bValid) {
    Write-Host "  -> PASS: Complete per-terminal isolation between Term A and Term B" -ForegroundColor Green
} else {
    Write-Host "Res A: $resA" -ForegroundColor Red
    Write-Host "Res B: $resB" -ForegroundColor Red
    Write-Error "FAIL: Isolation test failed!"
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "ALL POWERSHELL E2E INTEGRATION TESTS PASSED SUCCESSFULLY!   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
