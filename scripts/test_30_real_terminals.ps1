# 30 Real Independent PowerShell Processes Test
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   30 REAL INDEPENDENT POWERSHELL PROCESSES ISOLATION TEST" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$numTerms = 30
$results = @{}

Write-Host "Spawning $numTerms REAL independent powershell.exe processes in parallel..." -ForegroundColor Yellow

# Use PowerShell background jobs or runspaces to spawn 30 real independent powershell.exe processes
$jobs = @()

for ($i = 1; $i -le $numTerms; $i++) {
    $idx = $i.ToString('00')
    $marker = "REAL_TERMINAL_$idx"
    $script = @"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"
Write-Output "$marker"
Write-Output "Executing command in real process $idx"
python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout
"@

    $sb = [ScriptBlock]::Create("powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$script'")
    $jobs += [PSCustomObject]@{
        Index = $i
        Marker = $marker
        Job = Start-Job -ScriptBlock $sb
    }
}

Write-Host "Waiting for all $numTerms real processes to complete..." -ForegroundColor Yellow

$failures = 0

foreach ($j in $jobs) {
    $jobOutput = Receive-Job -Job $j.Job -Wait | Out-String
    Remove-Job -Job $j.Job -Force

    $expectedMarker = $j.Marker
    $i = $j.Index

    if ($jobOutput -notmatch "\b$expectedMarker\b") {
        Write-Host "[FAIL] Real Terminal $i missing marker $expectedMarker" -ForegroundColor Red
        $failures++
        continue
    }

    $leak = $false
    for ($k = 1; $k -le $numTerms; $k++) {
        if ($k -eq $i) { continue }
        $otherMarker = "REAL_TERMINAL_$($k.ToString('00'))"
        if ($jobOutput -match "\b$otherMarker\b") {
            Write-Host "[FAIL] Real Terminal $i leaked marker from Terminal $k ($otherMarker)!" -ForegroundColor Red
            $leak = $true
            $failures++
            break
        }
    }

    if (-not $leak) {
        Write-Host "  [OK] Real Terminal $i -> $expectedMarker only (100% Isolated)" -ForegroundColor Green
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
if ($failures -eq 0) {
    Write-Host "SUCCESS: All $numTerms REAL PowerShell processes verified 100% isolated!" -ForegroundColor Green
} else {
    Write-Host "FAILURE: Detected $failures isolation failures across real processes!" -ForegroundColor Red
    exit 1
}
Write-Host "============================================================`n" -ForegroundColor Cyan
