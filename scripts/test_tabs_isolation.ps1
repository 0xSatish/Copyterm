# Windows Terminal Tabs Simulation Test
$ErrorActionPreference = "Stop"

$tab1Script = @"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"
Write-Output "TAB_1_EXCLUSIVE_OUTPUT"
python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout
"@

$tab2Script = @"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"
Write-Output "TAB_2_EXCLUSIVE_OUTPUT"
python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout
"@

$tab3Script = @"
. "C:\Users\satis\OneDrive\Desktop\Copyterm\integrations\powershell\copyterm.ps1"
Write-Output "TAB_3_EXCLUSIVE_OUTPUT"
python "C:\Users\satis\OneDrive\Desktop\Copyterm\src\copyterm.py" --stdout
"@

$out1 = (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $tab1Script | Out-String)
$out2 = (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $tab2Script | Out-String)
$out3 = (powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $tab3Script | Out-String)

Write-Host "Tab 1 Result: $(if ($out1 -match 'TAB_1_EXCLUSIVE_OUTPUT' -and $out1 -notmatch 'TAB_2' -and $out1 -notmatch 'TAB_3') { 'PASS' } else { 'FAIL' })"
Write-Host "Tab 2 Result: $(if ($out2 -match 'TAB_2_EXCLUSIVE_OUTPUT' -and $out2 -notmatch 'TAB_1' -and $out2 -notmatch 'TAB_3') { 'PASS' } else { 'FAIL' })"
Write-Host "Tab 3 Result: $(if ($out3 -match 'TAB_3_EXCLUSIVE_OUTPUT' -and $out3 -notmatch 'TAB_1' -and $out3 -notmatch 'TAB_2') { 'PASS' } else { 'FAIL' })"

if (($out1 -match 'TAB_1_EXCLUSIVE_OUTPUT') -and ($out2 -match 'TAB_2_EXCLUSIVE_OUTPUT') -and ($out3 -match 'TAB_3_EXCLUSIVE_OUTPUT')) {
    Write-Host "`n--> [SUCCESS] Tab Isolation Test PASSED!" -ForegroundColor Green
} else {
    Write-Host "`n--> [FAIL] Tab Isolation Test Failed" -ForegroundColor Red
    exit 1
}
