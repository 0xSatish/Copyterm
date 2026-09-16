# ==============================================================================
# Build Script for Windows (PowerShell)
# ==============================================================================
param(
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"

Write-Host "Building copyterm (Windows $Configuration)..." -ForegroundColor Cyan

$srcFiles = @(
    "src/platform/environment.cpp",
    "src/platform/process.cpp",
    "src/platform/clipboard.cpp",
    "src/core/session.cpp",
    "src/core/ring_buffer.cpp",
    "src/core/sanitizer.cpp",
    "src/core/redaction.cpp",
    "src/core/formatter.cpp",
    "src/installer/installer.cpp",
    "src/cli/cli_args.cpp"
)

$optFlag = if ($Configuration -eq "Debug") { "-g -O0" } else { "-O2" }

# Build copyterm.exe
Write-Host "Compiling copyterm.exe..." -ForegroundColor Yellow
$mainCmd = "clang++ -std=c++17 $optFlag -Isrc src/cli/main.cpp $($srcFiles -join ' ') -o copyterm.exe -luser32 -lkernel32 -ladvapi32"
Invoke-Expression $mainCmd

# Build copyterm_tests.exe
Write-Host "Compiling copyterm_tests.exe..." -ForegroundColor Yellow
$testFiles = @(
    "tests/test_main.cpp",
    "tests/test_session.cpp",
    "tests/test_ring_buffer.cpp",
    "tests/test_sanitizer.cpp",
    "tests/test_redaction.cpp",
    "tests/test_formatter.cpp",
    "tests/test_isolation.cpp"
)
$testCmd = "clang++ -std=c++17 $optFlag -Isrc $($testFiles -join ' ') $($srcFiles -join ' ') -o copyterm_tests.exe -luser32 -lkernel32 -ladvapi32"
Invoke-Expression $testCmd

# Create cpt.exe alias binary
Copy-Item -Path "copyterm.exe" -Destination "cpt.exe" -Force

Write-Host "`nBuild complete successfully!" -ForegroundColor Green
Write-Host "  -> Binaries: cpt.exe, copyterm.exe, copyterm_tests.exe" -ForegroundColor Green
