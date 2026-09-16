. .\integrations\powershell\copyterm.ps1
Clear-Host
cmd.exe /c "echo TEST_LINE_ABC"
python src\copyterm.py --session-id $env:COPYTERM_SESSION_ID --stdout
