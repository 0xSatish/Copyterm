# ==============================================================================
# TEST: Antigravity IDE Historical Scrollback Capture
# Verifies that output generated BEFORE CopyTerm runs is 100% captured.
# ==============================================================================

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPy = Join-Path $env:USERPROFILE ".copyterm\bin\copyterm.py"
$pyScript = if (Test-Path $installedPy) { $installedPy } else { Join-Path $repoRoot "src\copyterm.py" }

Write-Host "=== TEST: Antigravity IDE Historical Scrollback Capture ===" -ForegroundColor Cyan

# 1. Emit historical markers BEFORE CopyTerm is invoked
Write-Host "Emitting historical markers..." -ForegroundColor Yellow
Write-Output "HISTORICAL_MARKER_A"
Write-Output "HISTORICAL_MARKER_B"
Write-Output "HISTORICAL_MARKER_C"

# 2. Emit 500 lines of historical scrollback
Write-Host "Generating 500 lines of historical scrollback..." -ForegroundColor Yellow
1..500 | ForEach-Object { "HISTORY_LINE_$_" }

# 3. Invoke CopyTerm
Write-Host "Running CopyTerm to capture buffer..." -ForegroundColor Yellow
$captured = python $pyScript --stdout

# 4. Verify markers
$pass = $true
$checks = @(
    "HISTORICAL_MARKER_A",
    "HISTORICAL_MARKER_B",
    "HISTORICAL_MARKER_C",
    "HISTORY_LINE_1",
    "HISTORY_LINE_250",
    "HISTORY_LINE_500"
)

foreach ($chk in $checks) {
    if ($captured -match [regex]::Escape($chk)) {
        Write-Host "  [PASS] Found marker: $chk" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Missing marker: $chk" -ForegroundColor Red
        $pass = $false
    }
}

if ($pass) {
    Write-Host "=== RESULT: HISTORICAL SCROLLBACK TEST PASSED ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== RESULT: HISTORICAL SCROLLBACK TEST FAILED ===" -ForegroundColor Red
    exit 1
}
