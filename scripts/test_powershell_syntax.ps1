$errors = $null
$tokens = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path "$PSScriptRoot\..\install.ps1"),
    [ref]$tokens,
    [ref]$errors
)

if ($errors -and $errors.Count -gt 0) {
    Write-Error "Parser errors found in install.ps1: $($errors | Out-String)"
    exit 1
} else {
    Write-Host "install.ps1: PARSER OK (0 errors)"
}

# Also test all other ps1 scripts in repository
$all_ps1 = Get-ChildItem -Path "$PSScriptRoot\.." -Filter "*.ps1" -Recurse
foreach ($f in $all_ps1) {
    $errs = $null
    $tks = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile(
        $f.FullName,
        [ref]$tks,
        [ref]$errs
    )
    if ($errs -and $errs.Count -gt 0) {
        Write-Error "Parser error in $($f.FullName): $($errs | Out-String)"
        exit 1
    } else {
        Write-Host "$($f.Name): PARSER OK"
    }
}
exit 0
