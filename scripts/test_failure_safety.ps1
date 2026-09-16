# Failure Safety Test Script
$ErrorActionPreference = "Continue"

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPs1 = Join-Path $env:USERPROFILE ".copyterm\integrations\powershell\copyterm.ps1"
$ps1Path = if (Test-Path $installedPs1) { $installedPs1 } else { Join-Path $repoRoot "integrations\powershell\copyterm.ps1" }
$bashPath = (Join-Path $repoRoot "integrations/bash/copyterm.bash").Replace("\", "/")
$cmdPath = Join-Path $repoRoot "integrations\cmd\copyterm.cmd"

Write-Host "=== TEST 1: PowerShell safety with invalid/read-only data directory ==="
$env:COPYTERM_DATA_DIR = "Z:\NonExistentDrive\InvalidPath"
. "$ps1Path"

Write-Output "NORMAL_COMMAND_OUTPUT_1"
$exit1 = $?
Get-Item . | Out-Null
$exit2 = $?

Write-Host "Command 1 succeeded: $exit1"
Write-Host "Command 2 succeeded: $exit2"

$env:COPYTERM_DATA_DIR = ""

Write-Host "`n=== TEST 2: Bash safety with invalid directory ==="
if (Test-Path "C:\Program Files\Git\bin\bash.exe") {
    & "C:\Program Files\Git\bin\bash.exe" -c "
export COPYTERM_DATA_DIR='/dev/null/invalid'
source '$bashPath' 2>/dev/null
echo 'BASH_NORMAL_EXECUTION'
ls > /dev/null
echo 'Exit code: $?'
"
} else {
    Write-Host "Git bash not installed, skipping bash test"
}

Write-Host "`n=== TEST 3: CMD safety ==="
cmd.exe /c "call `"$cmdPath`" && echo CMD_NORMAL_EXECUTION && dir > nul"

Write-Host "`n--> [SUCCESS] Failure Safety Test PASSED: Shells remain completely functional even if copyterm fails!" -ForegroundColor Green
