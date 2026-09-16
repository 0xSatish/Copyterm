# Real Clipboard Verification Script
$ErrorActionPreference = "Continue"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPs1 = Join-Path $env:USERPROFILE ".copyterm\integrations\powershell\copyterm.ps1"
$ps1Path = if (Test-Path $installedPs1) { $installedPs1 } else { Join-Path $repoRoot "integrations\powershell\copyterm.ps1" }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell.exe"
$psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command -"
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.UseShellExecute = $false

$proc = [System.Diagnostics.Process]::Start($psi)
$proc.StandardInput.WriteLine(". '$ps1Path'")
$proc.StandardInput.WriteLine("Write-Output 'CLIPBOARD_REAL_TEST_VERIFICATION_MARKER_789'")
$proc.StandardInput.WriteLine("cpt")
$proc.StandardInput.WriteLine("exit")
$proc.WaitForExit(5000)

Write-Host "`nRetrieving clipboard via separate Windows Forms and PowerShell API..."
Add-Type -AssemblyName System.Windows.Forms
$clip = [System.Windows.Forms.Clipboard]::GetText()

Write-Host "REAL OS CLIPBOARD CONTAINS:"
Write-Host "----------------------------------"
Write-Host $clip
Write-Host "----------------------------------"

if ($clip -match "CLIPBOARD_REAL_TEST_VERIFICATION_MARKER_789") {
    Write-Host "`n--> [SUCCESS] Clipboard Test PASSED: Verified actual clipboard contents contain the test marker!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] Clipboard Test FAILED: Marker not found in OS clipboard" -ForegroundColor Red
    exit 1
}
