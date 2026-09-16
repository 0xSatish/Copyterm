@echo off
:: ==============================================================================
:: COPYTERM — CMD Integration Script (Canonical cpt command)
:: CWD-Independent Architecture: Works from any working directory
:: Safe: No recursive process spawning
:: ==============================================================================

set "__COPYTERM_DATA_DIR=%USERPROFILE%\.copyterm"
set "__COPYTERM_BIN_DIR=%__COPYTERM_DATA_DIR%\bin"

:: 1. Check Python Core in same directory as this script (%~dp0)
if exist "%~dp0copyterm.py" (
    python "%~dp0copyterm.py" %*
    exit /b %ERRORLEVEL%
)

:: 2. Check ~/.copyterm/bin/cpt.exe
if exist "%__COPYTERM_BIN_DIR%\cpt.exe" (
    "%__COPYTERM_BIN_DIR%\cpt.exe" %*
    exit /b %ERRORLEVEL%
)

:: 3. Check ~/.copyterm/bin/copyterm.py
if exist "%__COPYTERM_BIN_DIR%\copyterm.py" (
    python "%__COPYTERM_BIN_DIR%\copyterm.py" %*
    exit /b %ERRORLEVEL%
)

:: 4. Check location relative to script directory (%~dp0)
if exist "%~dp0..\..\src\copyterm.py" (
    python "%~dp0..\..\src\copyterm.py" %*
    exit /b %ERRORLEVEL%
)

:: 5. Fallback to cpt.exe on PATH or python -m copyterm
cpt.exe %* 2>nul || python -m copyterm %*
