# ==============================================================================
# COPYTERM — Verification of Real-World Path Sequence (Requirement 23)
# ==============================================================================
$ErrorActionPreference = "Stop"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
. (Join-Path $repoRoot "integrations\powershell\copyterm.ps1")

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   COPYTERM REAL-WORLD PATH SEQUENCE VALIDATION (REQ 23)    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Phase 1: Clear + Cross-Directory Output Generation
Clear-Host

Write-Output "PATH_TEST_1"
Set-Location $env:USERPROFILE
Write-Output "PATH_TEST_2"
Set-Location (Join-Path $env:USERPROFILE "Downloads")
Write-Output "PATH_TEST_3"
Set-Location $repoRoot
Write-Output "PATH_TEST_4"

cpt

$clipText1 = ""
try {
    $clipText1 = Get-Clipboard -Raw
} catch {
    $clipText1 = (python -c "from src.copyterm import Clipboard; print(Clipboard.get_text())")
}

$p1 = ($clipText1 -match "PATH_TEST_1")
$p2 = ($clipText1 -match "PATH_TEST_2")
$p3 = ($clipText1 -match "PATH_TEST_3")
$p4 = ($clipText1 -match "PATH_TEST_4")

Write-Host "`nPhase 1 Results (Across directory navigation):" -ForegroundColor Yellow
Write-Host "  Clipboard contains PATH_TEST_1: $p1 (Expected: True)" -ForegroundColor $(if ($p1) { "Green" } else { "Red" })
Write-Host "  Clipboard contains PATH_TEST_2: $p2 (Expected: True)" -ForegroundColor $(if ($p2) { "Green" } else { "Red" })
Write-Host "  Clipboard contains PATH_TEST_3: $p3 (Expected: True)" -ForegroundColor $(if ($p3) { "Green" } else { "Red" })
Write-Host "  Clipboard contains PATH_TEST_4: $p4 (Expected: True)" -ForegroundColor $(if ($p4) { "Green" } else { "Red" })

if ($p1 -and $p2 -and $p3 -and $p4) {
    Write-Host "--> PASS: Phase 1 Succeeded!" -ForegroundColor Green
} else {
    Write-Error "FAIL: Phase 1 missing expected lines in clipboard"
}

# Phase 2: Clear + cd ~ + AFTER_CLEAR_HOME
Clear-Host
Set-Location $env:USERPROFILE
Write-Output "AFTER_CLEAR_HOME"

cpt

$clipText2 = ""
try {
    $clipText2 = Get-Clipboard -Raw
} catch {
    $clipText2 = (python -c "from src.copyterm import Clipboard; print(Clipboard.get_text())")
}

$hasAfterClearHome = ($clipText2 -match "AFTER_CLEAR_HOME")
$hasOldPathTest = ($clipText2 -match "PATH_TEST_")

Write-Host "`nPhase 2 Results (Clear + cd ~):" -ForegroundColor Yellow
Write-Host "  Clipboard contains AFTER_CLEAR_HOME: $hasAfterClearHome (Expected: True)" -ForegroundColor $(if ($hasAfterClearHome) { "Green" } else { "Red" })
Write-Host "  Clipboard contains old PATH_TEST:    $hasOldPathTest (Expected: False)" -ForegroundColor $(if (-not $hasOldPathTest) { "Green" } else { "Red" })

if ($hasAfterClearHome -and (-not $hasOldPathTest)) {
    Write-Host "--> PASS: Phase 2 Succeeded!" -ForegroundColor Green
} else {
    Write-Error "FAIL: Phase 2 failed (contained old data or missed new data)"
}

# Phase 3: cd back to project and capture again
Set-Location $repoRoot
cpt

$clipText3 = ""
try {
    $clipText3 = Get-Clipboard -Raw
} catch {
    $clipText3 = (python -c "from src.copyterm import Clipboard; print(Clipboard.get_text())")
}

$stillHasAfterClear = ($clipText3 -match "AFTER_CLEAR_HOME")
$stillNoOldPathTest = (-not ($clipText3 -match "PATH_TEST_"))

Write-Host "`nPhase 3 Results (cd back to repo):" -ForegroundColor Yellow
Write-Host "  Clipboard still contains AFTER_CLEAR_HOME: $stillHasAfterClear (Expected: True)" -ForegroundColor $(if ($stillHasAfterClear) { "Green" } else { "Red" })
Write-Host "  Clipboard still excludes PATH_TEST:        $stillNoOldPathTest (Expected: True)" -ForegroundColor $(if ($stillNoOldPathTest) { "Green" } else { "Red" })

if ($stillHasAfterClear -and $stillNoOldPathTest) {
    Write-Host "--> PASS: Phase 3 Succeeded!" -ForegroundColor Green
} else {
    Write-Error "FAIL: Phase 3 failed"
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "ALL REAL-WORLD PATH SEQUENCE VALIDATION TESTS PASSED!       " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
