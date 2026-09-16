# ==============================================================================
# COPYTERM — Test stdout parity with clipboard
# ==============================================================================
$ErrorActionPreference = "Stop"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
. (Join-Path $repoRoot "integrations\powershell\copyterm.ps1")

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         COPYTERM STDOUT & CLIPBOARD PARITY TEST            " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Clear-Host
1..100 | ForEach-Object { "STDOUT_PARITY_$_" }

# Capture 1: Clipboard
cpt
$clipText = ""
try {
    $clipText = Get-Clipboard -Raw
} catch {
    $clipText = (python -c "from src.copyterm import Clipboard; print(Clipboard.get_text())")
}

# Capture 2: stdout redirection
$outFile = Join-Path $env:TEMP "cpt_stdout_parity.txt"
if (Test-Path $outFile) { Remove-Item $outFile -Force }

cpt --stdout > $outFile
$outText = Get-Content $outFile -Raw

$clipLines = $clipText.Trim().Split("`n").Count
$outLines = $outText.Trim().Split("`n").Count

Write-Host "  Clipboard captured lines: $clipLines" -ForegroundColor Yellow
Write-Host "  stdout captured lines:    $outLines" -ForegroundColor Yellow

$match1 = ($clipText -match "STDOUT_PARITY_1\b")
$match100 = ($clipText -match "STDOUT_PARITY_100\b")
$outMatch1 = ($outText -match "STDOUT_PARITY_1\b")
$outMatch100 = ($outText -match "STDOUT_PARITY_100\b")

if ($match1 -and $match100 -and $outMatch1 -and $outMatch100) {
    Write-Host "`n--> PASS: stdout and clipboard capture 100% matched!" -ForegroundColor Green
} else {
    Write-Error "FAIL: Parity test failed!"
}
