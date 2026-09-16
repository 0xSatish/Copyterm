# ==============================================================================
# COPYTERM — Windows Uninstaller
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$Quiet
)

$repoRoot = $PSScriptRoot
if (-not $repoRoot) { $repoRoot = (Get-Location).Path }

$installScript = Join-Path $repoRoot "install.ps1"
if (Test-Path $installScript) {
    & $installScript -Uninstall $(if ($Quiet) { "-Quiet" })
} else {
    python (Join-Path $repoRoot "install.py") --uninstall $(if ($Quiet) { "--quiet" })
}
