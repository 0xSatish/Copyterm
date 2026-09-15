# Real Long Output Test
$ErrorActionPreference = "Continue"

. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"

Write-Host "Emitting 1,000 lines..."
1..1000 | ForEach-Object { "REAL_LINE_$_" }

Write-Host "`nQuerying copyterm --stdout..."
$captured = (& python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout | Out-String)

$hasLine1 = $captured -match "\bREAL_LINE_1\b"
$hasLine500 = $captured -match "\bREAL_LINE_500\b"
$hasLine1000 = $captured -match "\bREAL_LINE_1000\b"

Write-Host "REAL_LINE_1 present: $hasLine1"
Write-Host "REAL_LINE_500 present: $hasLine500"
Write-Host "REAL_LINE_1000 present: $hasLine1000"

if ($hasLine1 -and $hasLine500 -and $hasLine1000) {
    Write-Host "`n--> [SUCCESS] Long output test PASSED: 1,000 lines captured cleanly!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] Long output test failed" -ForegroundColor Red
    exit 1
}
