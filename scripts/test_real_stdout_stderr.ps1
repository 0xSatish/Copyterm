# Real Stdout + Stderr Capture Test
$ErrorActionPreference = "Continue"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
. (Join-Path $repoRoot "integrations\powershell\copyterm.ps1")

Write-Output "STDOUT_TEST"
Write-Error "STDERR_TEST" -ErrorAction Continue

$captured = (& python (Join-Path $repoRoot "src\copyterm.py") --stdout | Out-String)

Write-Host "`n=== INSPECTING CAPTURED STREAM ==="
Write-Host $captured
Write-Host "=================================="

$hasStdout = $captured -match "STDOUT_TEST"
$hasStderr = $captured -match "STDERR_TEST"

Write-Host "STDOUT captured: $hasStdout"
Write-Host "STDERR captured: $hasStderr"

if ($hasStdout -and $hasStderr) {
    Write-Host "`n--> [SUCCESS] Both STDOUT and STDERR were captured successfully!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] Failed to capture both streams" -ForegroundColor Red
    exit 1
}
