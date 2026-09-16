# ==============================================================================
# TEST: Antigravity IDE Wrapped Lines & Unicode Test
# ==============================================================================

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPy = Join-Path $env:USERPROFILE ".copyterm\bin\copyterm.py"
$pyScript = if (Test-Path $installedPy) { $installedPy } else { Join-Path $repoRoot "src\copyterm.py" }

Write-Host "=== TEST: Antigravity IDE Wrapped Lines & Unicode ===" -ForegroundColor Cyan

# 1. Long continuous string (500 chars)
$longString = "LONG_PREFIX_" + ("X" * 480) + "_LONG_SUFFIX"
Write-Output $longString

# 2. Unicode and emoji
$unicodeString = "UNICODE_TEST_こんにちは_🚀_世界_✓_★_2026"
Write-Output $unicodeString

# 3. Capture via CopyTerm
$captured = python $pyScript --stdout

$pass = $true
if ($captured -match "LONG_PREFIX_X{480}_LONG_SUFFIX") {
    Write-Host "  [PASS] 500-char continuous line unwrapped correctly" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Continuous line was incorrectly split or corrupted" -ForegroundColor Red
    $pass = $false
}

if ($captured -match "UNICODE_TEST_こんにちは_🚀_世界_✓_★_2026") {
    Write-Host "  [PASS] Unicode characters and emojis preserved intact" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Unicode characters corrupted" -ForegroundColor Red
    $pass = $false
}

if ($pass) {
    Write-Host "=== RESULT: WRAPPED LINES & UNICODE TEST PASSED ===" -ForegroundColor Green
    exit 0
} else {
    Write-Host "=== RESULT: WRAPPED LINES & UNICODE TEST FAILED ===" -ForegroundColor Red
    exit 1
}
