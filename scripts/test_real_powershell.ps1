# Real PowerShell Test Script
$ErrorActionPreference = "Continue"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
. (Join-Path $repoRoot "integrations\powershell\copyterm.ps1")

Write-Host "`n=== STEP 2: Run Write-Output COPYTERM_REAL_TEST_001 ==="
Write-Output "COPYTERM_REAL_TEST_001"

Write-Host "`n=== STEP 3: Run copyterm --stdout ==="
copyterm --stdout

Write-Host "`n=== STEP 4: Run Get-ChildItem -Name ==="
Get-ChildItem -Name

Write-Host "`n=== STEP 5: Run copyterm --stdout (Check 2) ==="
copyterm --stdout

Write-Host "`n=== STEP 6: Run Write-Output COPYTERM_REAL_TEST_002 and copyterm ==="
Write-Output "COPYTERM_REAL_TEST_002"
copyterm

Write-Host "`n=== STEP 7: Inspect Real Clipboard Content ==="
Add-Type -AssemblyName System.Windows.Forms
$clipText = [System.Windows.Forms.Clipboard]::GetText()
Write-Host "CLIPBOARD CONTENT BEGIN:" -ForegroundColor Cyan
Write-Host $clipText
Write-Host "CLIPBOARD CONTENT END" -ForegroundColor Cyan

if ($clipText -match "COPYTERM_REAL_TEST_001" -and $clipText -match "COPYTERM_REAL_TEST_002" -and $clipText -match "CMakeLists.txt") {
    Write-Host "`n--> [SUCCESS] Real PowerShell Test PASSED: All commands, stdout, and files captured to clipboard!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] Real PowerShell Test FAILED" -ForegroundColor Red
}
