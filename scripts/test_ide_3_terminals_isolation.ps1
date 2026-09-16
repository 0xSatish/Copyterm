# ==============================================================================
# TEST: 3-Terminal Isolation in CopyTerm
# Verifies that Terminal A != Terminal B != Terminal C (0% Cross-Contamination)
# ==============================================================================

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPy = Join-Path $env:USERPROFILE ".copyterm\bin\copyterm.py"
$pyScript = if (Test-Path $installedPy) { $installedPy } else { Join-Path $repoRoot "src\copyterm.py" }
$dataDir = Join-Path $env:USERPROFILE ".copyterm"
$sessDir = Join-Path $dataDir "sessions"

Write-Host "=== TEST: 3-Terminal Isolation in CopyTerm ===" -ForegroundColor Cyan

$termA_Id = "sess_test_term_A_111"
$termB_Id = "sess_test_term_B_222"
$termC_Id = "sess_test_term_C_333"

# Create simulated independent terminal buffers
[System.IO.File]::WriteAllText((Join-Path $sessDir "$termA_Id.buf"), "TERMINAL_A_UNIQUE_MARKER_AAA`nCOMMAND_A_OUTPUT")
[System.IO.File]::WriteAllText((Join-Path $sessDir "$termA_Id.meta"), "session_id=$termA_Id`npid=1001`nshell_name=powershell")

[System.IO.File]::WriteAllText((Join-Path $sessDir "$termB_Id.buf"), "TERMINAL_B_UNIQUE_MARKER_BBB`nCOMMAND_B_OUTPUT")
[System.IO.File]::WriteAllText((Join-Path $sessDir "$termB_Id.meta"), "session_id=$termB_Id`npid=2002`nshell_name=powershell")

[System.IO.File]::WriteAllText((Join-Path $sessDir "$termC_Id.buf"), "TERMINAL_C_UNIQUE_MARKER_CCC`nCOMMAND_C_OUTPUT")
[System.IO.File]::WriteAllText((Join-Path $sessDir "$termC_Id.meta"), "session_id=$termC_Id`npid=3003`nshell_name=powershell")

$pass = $true

# Test Terminal A
$outA = python $pyScript --session-id $termA_Id --stdout
if ($outA -match "TERMINAL_A_UNIQUE_MARKER_AAA" -and $outA -notmatch "TERMINAL_B_UNIQUE_MARKER_BBB" -and $outA -notmatch "TERMINAL_C_UNIQUE_MARKER_CCC") {
    Write-Host "  [PASS] Terminal A captured strictly its own buffer" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Terminal A contained cross-talk from B or C" -ForegroundColor Red
    $pass = $false
}

# Test Terminal B
$outB = python $pyScript --session-id $termB_Id --stdout
if ($outB -match "TERMINAL_B_UNIQUE_MARKER_BBB" -and $outB -notmatch "TERMINAL_A_UNIQUE_MARKER_AAA" -and $outB -notmatch "TERMINAL_C_UNIQUE_MARKER_CCC") {
    Write-Host "  [PASS] Terminal B captured strictly its own buffer" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Terminal B contained cross-talk from A or C" -ForegroundColor Red
    $pass = $false
}

# Test Terminal C
$outC = python $pyScript --session-id $termC_Id --stdout
if ($outC -match "TERMINAL_C_UNIQUE_MARKER_CCC" -and $outC -notmatch "TERMINAL_A_UNIQUE_MARKER_AAA" -and $outC -notmatch "TERMINAL_B_UNIQUE_MARKER_BBB") {
    Write-Host "  [PASS] Terminal C captured strictly its own buffer" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Terminal C contained cross-talk from A or B" -ForegroundColor Red
    $pass = $false
}

# Clean up temporary test sessions
Remove-Item -Force (Join-Path $sessDir "$termA_Id.*") -ErrorAction SilentlyContinue
Remove-Item -Force (Join-Path $sessDir "$termB_Id.*") -ErrorAction SilentlyContinue
Remove-Item -Force (Join-Path $sessDir "$termC_Id.*") -ErrorAction SilentlyContinue

if ($pass) {
    Write-Host "=== RESULT: 3-TERMINAL ISOLATION TEST PASSED ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== RESULT: 3-TERMINAL ISOLATION TEST FAILED ===" -ForegroundColor Red
    exit 1
}
