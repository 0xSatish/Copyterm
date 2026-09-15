# Real ANSI / VT Output Test Script
$ErrorActionPreference = "Continue"

$esc = [char]27
$cr = [char]13
$lf = [char]10

# Construct raw byte sequence: RED_ERROR_MESSAGE + GREEN_SUCCESS + progress bar \r overwrite
$rawString = "${esc}[31mRED_ERROR_MESSAGE${esc}[0m and ${esc}[32mGREEN_SUCCESS${esc}[0m${lf}[=>   ] 25%${cr}[====] 100%${lf}"
$rawBytes = [System.Text.Encoding]::UTF8.GetBytes($rawString)

$sessId = "sess_ansi_real_test"
$bufFile = [System.IO.Path]::Combine($env:USERPROFILE, ".copyterm", "sessions", "$sessId.buf")
[System.IO.File]::WriteAllBytes($bufFile, $rawBytes)

Write-Host "=== TEST 1: copyterm --clean --stdout ==="
$clean = (& python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --session-id $sessId --clean --stdout | Out-String)
Write-Host "Clean output: $clean"

Write-Host "=== TEST 2: copyterm --raw --stdout ==="
$raw = (& python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --session-id $sessId --raw --stdout | Out-String)
Write-Host "Raw output: $raw"

Remove-Item $bufFile -Force

$cleanHasNoEsc = (-not ($clean.Contains($esc)))
$cleanHasNoProgressBarOld = (-not ($clean.Contains("[=>   ] 25%")))
$cleanHasProgressBarFinal = ($clean.Contains("[====] 100%"))
$rawHasEsc = ($raw.Contains($esc))

Write-Host "Clean mode stripped ANSI escapes: $cleanHasNoEsc"
Write-Host "Clean mode removed old progress state: $cleanHasNoProgressBarOld"
Write-Host "Clean mode kept final progress state: $cleanHasProgressBarFinal"
Write-Host "Raw mode preserved ANSI escapes: $rawHasEsc"

if ($cleanHasNoEsc -and $cleanHasNoProgressBarOld -and $cleanHasProgressBarFinal -and $rawHasEsc) {
    Write-Host "`n--> [SUCCESS] ANSI / VT processing test PASSED!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] ANSI test failed" -ForegroundColor Red
    exit 1
}
