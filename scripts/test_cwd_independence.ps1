# ==============================================================================
# COPYTERM — CWD & Directory Path Independence Test Suite
# ==============================================================================
$ErrorActionPreference = "Stop"
$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$origLocation = (Get-Location).Path

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "      COPYTERM CWD & PATH INDEPENDENCE TEST SUITE           " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Source integration
. (Join-Path $repoRoot "integrations\powershell\copyterm.ps1")

$testDirs = @(
    $env:USERPROFILE,
    (Join-Path $env:USERPROFILE "Downloads"),
    $repoRoot,
    $env:TEMP
)

# Test 1: Executable & Command Resolution from multiple directories
Write-Host "`n[Test 1] Testing command resolution from multiple directories..." -ForegroundColor Yellow
foreach ($dir in $testDirs) {
    if (Test-Path $dir) {
        Set-Location $dir
        $resolvedCpt = Get-Command cpt -ErrorAction SilentlyContinue
        $resolvedCopyterm = Get-Command copyterm -ErrorAction SilentlyContinue
        if ($resolvedCpt -and $resolvedCopyterm) {
            Write-Host "  -> PASS: cpt & copyterm resolved from $dir" -ForegroundColor Green
        } else {
            Write-Error "FAIL: Command resolution failed in $dir"
        }
    }
}

# Test 2: Session Identity stability across cd
Write-Host "`n[Test 2] Verifying session identity and epoch stability across cd..." -ForegroundColor Yellow
$origSessionId = $env:COPYTERM_SESSION_ID
$origEpoch = $global:__copyterm_epoch

Set-Location $env:USERPROFILE
$s1 = $env:COPYTERM_SESSION_ID
$e1 = $global:__copyterm_epoch

Set-Location (Join-Path $env:USERPROFILE "Downloads")
$s2 = $env:COPYTERM_SESSION_ID
$e2 = $global:__copyterm_epoch

Set-Location $repoRoot
$s3 = $env:COPYTERM_SESSION_ID
$e3 = $global:__copyterm_epoch

Set-Location $env:TEMP
$s4 = $env:COPYTERM_SESSION_ID
$e4 = $global:__copyterm_epoch

if ($s1 -eq $origSessionId -and $s2 -eq $origSessionId -and $s3 -eq $origSessionId -and $s4 -eq $origSessionId -and
    $e1 -eq $origEpoch -and $e2 -eq $origEpoch -and $e3 -eq $origEpoch -and $e4 -eq $origEpoch) {
    Write-Host "  -> PASS: Session ID ($origSessionId) and Epoch ($origEpoch) remained strictly stable across cd" -ForegroundColor Green
} else {
    Write-Error "FAIL: Session ID or Epoch was mutated by cd!"
}

# Test 3: Directory stack operations (pushd / popd)
Write-Host "`n[Test 3] Testing pushd and popd directory stack operations..." -ForegroundColor Yellow
Push-Location $env:USERPROFILE
cmd.exe /c "echo PUSHD_TEST_LINE"
Pop-Location
cmd.exe /c "echo POPD_TEST_LINE"

if ($env:COPYTERM_SESSION_ID -eq $origSessionId) {
    Write-Host "  -> PASS: Session ID remained stable across pushd / popd" -ForegroundColor Green
} else {
    Write-Error "FAIL: Session ID corrupted by pushd / popd!"
}

# Test 4: Capture output generated across multiple directory transitions
Write-Host "`n[Test 4] Testing output capture across multiple directory transitions..." -ForegroundColor Yellow
Clear-Host # New Epoch
$currEpoch = $global:__copyterm_epoch

cmd.exe /c "echo DIR_TEST_START"
Set-Location $env:USERPROFILE
cmd.exe /c "echo AFTER_CD_HOME"
Set-Location (Join-Path $env:USERPROFILE "Downloads")
cmd.exe /c "echo AFTER_CD_DOWNLOADS"
Set-Location $repoRoot
cmd.exe /c "echo AFTER_CD_COPYTERM"
Set-Location $env:TEMP
cmd.exe /c "echo AFTER_CD_TEMP"

# Capture via cpt --stdout
$captureFile = Join-Path $env:TEMP "cpt_cwd_test_output.txt"
if (Test-Path $captureFile) { Remove-Item $captureFile -Force }

cpt --session-id $env:COPYTERM_SESSION_ID --stdout > $captureFile
$capturedText = Get-Content $captureFile -Raw

$allPresent = ($capturedText -match "DIR_TEST_START") -and `
              ($capturedText -match "AFTER_CD_HOME") -and `
              ($capturedText -match "AFTER_CD_DOWNLOADS") -and `
              ($capturedText -match "AFTER_CD_COPYTERM") -and `
              ($capturedText -match "AFTER_CD_TEMP")

if ($allPresent) {
    Write-Host "  -> PASS: All output across 4 directory changes captured completely" -ForegroundColor Green
} else {
    Write-Host "Captured output:`n$capturedText" -ForegroundColor Magenta
    Write-Error "FAIL: Captured output missing expected lines across directory transitions!"
}

# Test 5: Clear boundary with subsequent directory transitions
Write-Host "`n[Test 5] Testing clear boundary with directory transitions..." -ForegroundColor Yellow
cmd.exe /c "echo OLD_DIR_DATA_1"
cmd.exe /c "echo OLD_DIR_DATA_2"

Clear-Host # Advance epoch
Set-Location $env:USERPROFILE
cmd.exe /c "echo POST_CLEAR_HOME_LINE"
Set-Location (Join-Path $env:USERPROFILE "Downloads")
cmd.exe /c "echo POST_CLEAR_DOWNLOADS_LINE"

$captureFile2 = Join-Path $env:TEMP "cpt_cwd_test_output2.txt"
if (Test-Path $captureFile2) { Remove-Item $captureFile2 -Force }

cpt --session-id $env:COPYTERM_SESSION_ID --stdout > $captureFile2
$capturedText2 = Get-Content $captureFile2 -Raw

$oldExcluded = ($capturedText2 -notmatch "OLD_DIR_DATA")
$newIncluded = ($capturedText2 -match "POST_CLEAR_HOME_LINE") -and ($capturedText2 -match "POST_CLEAR_DOWNLOADS_LINE")

if ($oldExcluded -and $newIncluded) {
    Write-Host "  -> PASS: Pre-clear data excluded and post-clear cross-directory data captured" -ForegroundColor Green
} else {
    Write-Host "Captured text 2:`n$capturedText2" -ForegroundColor Magenta
    Write-Error "FAIL: Clear boundary failed during directory transitions!"
}

# Restore original location
Set-Location $origLocation

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "ALL CWD INDEPENDENCE TESTS PASSED SUCCESSFULLY!             " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
