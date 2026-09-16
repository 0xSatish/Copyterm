# ==============================================================================
# COPYTERM — Verification of Manual Test 1 & 2 (Clear Boundary + 500 & 2000 Lines)
# ==============================================================================
$ErrorActionPreference = "Stop"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPs1 = Join-Path $env:USERPROFILE ".copyterm\integrations\powershell\copyterm.ps1"
$ps1Path = if (Test-Path $installedPs1) { $installedPs1 } else { Join-Path $repoRoot "integrations\powershell\copyterm.ps1" }
. "$ps1Path"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       COPYTERM MANUAL TEST 1 & 2 VERIFICATION              " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: Generate Old Content
Write-Output "COPYTERM_OLD_START"
1..100 | ForEach-Object { "COPYTERM_OLD_$_" }
Write-Output "COPYTERM_OLD_END"

# Step 2: Clear Boundary
Clear-Host

# Step 3: Generate New Content (500 lines)
Write-Output "COPYTERM_NEW_START"
1..500 | ForEach-Object { "COPYTERM_NEW_$_" }
Write-Output "COPYTERM_NEW_END"

# Step 4: Run cpt to clipboard
cpt

# Step 5: Verify Clipboard Content
$clipText = ""
try {
    $clipText = Get-Clipboard -Raw
} catch {
    $clipText = (python -c "from src.copyterm import Clipboard; print(Clipboard.get_text())")
}

$hasOld = ($clipText -match "COPYTERM_OLD_")
$hasNewStart = ($clipText -match "COPYTERM_NEW_START")
$hasNewEnd = ($clipText -match "COPYTERM_NEW_END")
$hasNew1 = ($clipText -match "COPYTERM_NEW_1")
$hasNew500 = ($clipText -match "COPYTERM_NEW_500")

Write-Host "  hasOld:      $hasOld"
Write-Host "  hasNewStart: $hasNewStart"
Write-Host "  hasNewEnd:   $hasNewEnd"
Write-Host "  hasNew1:     $hasNew1"
Write-Host "  hasNew500:   $hasNew500"

if (-not $hasOld -and $hasNewStart -and $hasNewEnd -and $hasNew1 -and $hasNew500) {
    Write-Host "`n--> PASS: Manual Test 1 (500 lines after clear) SUCCEEDED!" -ForegroundColor Green
} else {
    Write-Error "FAIL: Manual Test 1 failed!"
}

# Step 6: Test 2 (2000 lines historical scrollback after clear)
Clear-Host
1..2000 | ForEach-Object { "AFTER_CLEAR_$_" }

cpt

$clipText2 = ""
try {
    $clipText2 = Get-Clipboard -Raw
} catch {
    $clipText2 = (python -c "from src.copyterm import Clipboard; print(Clipboard.get_text())")
}
$has2k_1 = ($clipText2 -match "AFTER_CLEAR_1\b")
$has2k_1000 = ($clipText2 -match "AFTER_CLEAR_1000\b")
$has2k_2000 = ($clipText2 -match "AFTER_CLEAR_2000\b")
$hasOld500 = ($clipText2 -match "COPYTERM_NEW_")

Write-Host "`nResults for Manual Test 2 (2000 lines after clear):" -ForegroundColor Yellow
Write-Host "  Clipboard contains AFTER_CLEAR_1:   $has2k_1 (Expected: True)" -ForegroundColor $(if ($has2k_1) { "Green" } else { "Red" })
Write-Host "  Clipboard contains AFTER_CLEAR_1000:$has2k_1000 (Expected: True)" -ForegroundColor $(if ($has2k_1000) { "Green" } else { "Red" })
Write-Host "  Clipboard contains AFTER_CLEAR_2000:$has2k_2000 (Expected: True)" -ForegroundColor $(if ($has2k_2000) { "Green" } else { "Red" })
Write-Host "  Clipboard contains old epoch data:  $hasOld500 (Expected: False)" -ForegroundColor $(if (-not $hasOld500) { "Green" } else { "Red" })

if ($has2k_1 -and $has2k_1000 -and $has2k_2000 -and -not $hasOld500) {
    Write-Host "`n--> PASS: Manual Test 2 (2000 lines after clear) SUCCEEDED!" -ForegroundColor Green
} else {
    Write-Error "FAIL: Manual Test 2 failed!"
}
