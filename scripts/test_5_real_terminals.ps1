# 5 Real Independent PowerShell Processes Test
$ErrorActionPreference = "Stop"

Write-Host "Spawning 5 REAL independent PowerShell processes..." -ForegroundColor Cyan

$numTerms = 5
$results = @{}

$repoRoot = if ($PSScriptRoot) { (Resolve-Path "$PSScriptRoot\..").Path } else { (Get-Location).Path }
$installedPs1 = Join-Path $env:USERPROFILE ".copyterm\integrations\powershell\copyterm.ps1"
$ps1Path = if (Test-Path $installedPs1) { $installedPs1 } else { Join-Path $repoRoot "integrations\powershell\copyterm.ps1" }
$installedPy = Join-Path $env:USERPROFILE ".copyterm\bin\copyterm.py"
$pyScript = if (Test-Path $installedPy) { $installedPy } else { Join-Path $repoRoot "src\copyterm.py" }

for ($i = 1; $i -le $numTerms; $i++) {
    $marker = "REAL_SESSION_0$i"
    $script = @"
. "$ps1Path"
Write-Output "$marker"
python "$pyScript" --stdout
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
