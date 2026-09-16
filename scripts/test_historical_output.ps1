# Historical Output Test
$ErrorActionPreference = "Continue"

Write-Output "BEFORE_COPYTERM_TEST"
Write-Output "COMMAND_BEFORE_CAPTURE_1"
Write-Output "COMMAND_BEFORE_CAPTURE_2"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPs1 = Join-Path $env:USERPROFILE ".copyterm\integrations\powershell\copyterm.ps1"
$ps1Path = if (Test-Path $installedPs1) { $installedPs1 } else { Join-Path $repoRoot "integrations\powershell\copyterm.ps1" }
$installedPy = Join-Path $env:USERPROFILE ".copyterm\bin\copyterm.py"
$pyScript = if (Test-Path $installedPy) { $installedPy } else { Join-Path $repoRoot "src\copyterm.py" }

Write-Host "`n[Action] Initializing copyterm integration now...`n"
. "$ps1Path"

Write-Output "AFTER_COPYTERM_TEST"

Write-Host "`n=== RESULT OF copyterm --stdout ==="
$output = (& python "$pyScript" --stdout | Out-String)
Write-Host $output
Write-Host "==================================="

$hasBefore = $output -match "\bBEFORE_COPYTERM_TEST\b"
$hasAfter = $output -match "\bAFTER_COPYTERM_TEST\b"

Write-Host "BEFORE_COPYTERM_TEST available: $hasBefore"
Write-Host "AFTER_COPYTERM_TEST available: $hasAfter"

if (-not $hasBefore -and $hasAfter) {
    Write-Host "`n--> [CONFIRMED REALITY] Output generated before capture initialization cannot be recovered on standard non-tmux terminals." -ForegroundColor Yellow
}
