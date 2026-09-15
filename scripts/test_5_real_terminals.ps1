# 5 Real Independent PowerShell Processes Test
$ErrorActionPreference = "Stop"

Write-Host "Spawning 5 REAL independent PowerShell processes..." -ForegroundColor Cyan

$numTerms = 5
$results = @{}

for ($i = 1; $i -le $numTerms; $i++) {
    $marker = "REAL_SESSION_0$i"
    $script = @"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"
Write-Output "$marker"
python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout
"@

    # Spawn actual independent powershell.exe process
    $output = (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $script | Out-String)
    $results[$i] = $output
}

Write-Host "`nVerifying isolation across all 5 real PowerShell sessions..." -ForegroundColor Yellow
$failures = 0

for ($i = 1; $i -le $numTerms; $i++) {
    $out = $results[$i]
    $expectedMarker = "REAL_SESSION_0$i"

    if ($out -notmatch "\b$expectedMarker\b") {
        Write-Host "[FAIL] Terminal $i is missing expected marker $expectedMarker" -ForegroundColor Red
        $failures++
        continue
    }

    $leak = $false
    for ($j = 1; $j -le $numTerms; $j++) {
        if ($i -eq $j) { continue }
        $otherMarker = "REAL_SESSION_0$j"
        if ($out -match "\b$otherMarker\b") {
            Write-Host "[FAIL] Terminal $i contains leaked marker from Terminal $j ($otherMarker)!" -ForegroundColor Red
            $leak = $true
            $failures++
            break
        }
    }

    if (-not $leak) {
        Write-Host "  [OK] Terminal $i -> $expectedMarker only (100% Isolated)" -ForegroundColor Green
    }
}

if ($failures -eq 0) {
    Write-Host "`n--> [SUCCESS] All 5 REAL PowerShell terminals verified with ZERO cross-contamination!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] 5-terminal test failed with $failures errors" -ForegroundColor Red
    exit 1
}
