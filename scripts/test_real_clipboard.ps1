# Real Clipboard Verification Script
$ErrorActionPreference = "Continue"

. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"

Write-Output "CLIPBOARD_REAL_TEST_VERIFICATION_MARKER_789"
copyterm

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
