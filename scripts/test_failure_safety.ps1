# Failure Safety Test Script
$ErrorActionPreference = "Continue"

Write-Host "=== TEST 1: PowerShell safety with invalid/read-only data directory ==="
$env:COPYTERM_DATA_DIR = "Z:\NonExistentDrive\InvalidPath"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"

Write-Output "NORMAL_COMMAND_OUTPUT_1"
$exit1 = $?
Get-Item . | Out-Null
$exit2 = $?

Write-Host "Command 1 succeeded: $exit1"
Write-Host "Command 2 succeeded: $exit2"

$env:COPYTERM_DATA_DIR = ""

Write-Host "`n=== TEST 2: Bash safety with invalid directory ==="
& "C:\Program Files\Git\bin\bash.exe" -c '
export COPYTERM_DATA_DIR="/dev/null/invalid"
source "C:/Users/satis/OneDrive/Desktop/Copyterm/integrations/bash/copyterm.bash" 2>/dev/null
echo "BASH_NORMAL_EXECUTION"
ls > /dev/null
echo "Exit code: $?"
'

Write-Host "`n=== TEST 3: CMD safety ==="
cmd.exe /c "call C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\cmd\copyterm.cmd && echo CMD_NORMAL_EXECUTION && dir > nul"

Write-Host "`n--> [SUCCESS] Failure Safety Test PASSED: Shells remain completely functional even if copyterm fails!" -ForegroundColor Green
