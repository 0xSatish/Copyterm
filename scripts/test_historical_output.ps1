# Historical Output Test
$ErrorActionPreference = "Continue"

Write-Output "BEFORE_COPYTERM_TEST"
Write-Output "COMMAND_BEFORE_CAPTURE_1"
Write-Output "COMMAND_BEFORE_CAPTURE_2"

Write-Host "`n[Action] Initializing copyterm integration now...`n"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"

Write-Output "AFTER_COPYTERM_TEST"

Write-Host "`n=== RESULT OF copyterm --stdout ==="
$output = (& python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout | Out-String)
Write-Host $output
Write-Host "==================================="

$hasBefore = $output -match "\bBEFORE_COPYTERM_TEST\b"
$hasAfter = $output -match "\bAFTER_COPYTERM_TEST\b"

Write-Host "BEFORE_COPYTERM_TEST available: $hasBefore"
Write-Host "AFTER_COPYTERM_TEST available: $hasAfter"

if (-not $hasBefore -and $hasAfter) {
    Write-Host "`n--> [CONFIRMED REALITY] Output generated before capture initialization cannot be recovered on standard non-tmux terminals." -ForegroundColor Yellow
}
