@echo off
:: ==============================================================================
:: COPYTERM — CMD Integration Script (Canonical cpt command)
:: CWD-Independent Architecture: Works from any working directory
:: ==============================================================================

if "%COPYTERM_SESSION_ID%"=="" (
    set "__CPT_DATA_DIR=%USERPROFILE%\.copyterm"
    set "__CPT_BIN_DIR=%__CPT_DATA_DIR%\bin"
    if exist "%__CPT_BIN_DIR%\copyterm.py" (
        for /f "usebackq tokens=*" %%i in (`python "%__CPT_BIN_DIR%\copyterm.py" --init-session cmd 2^>nul`) do (
            set "COPYTERM_SESSION_ID=%%i"
        )
    ) else if exist "%~dp0..\..\src\copyterm.py" (
        for /f "usebackq tokens=*" %%i in (`python "%~dp0..\..\src\copyterm.py" --init-session cmd 2^>nul`) do (
            set "COPYTERM_SESSION_ID=%%i"
        )
    )
    if "%COPYTERM_SESSION_ID%"=="" (
        set "COPYTERM_SESSION_ID=sess_%RANDOM%_%RANDOM%"
    )
)

set "__COPYTERM_DATA_DIR=%USERPROFILE%\.copyterm"
set "__COPYTERM_SESSIONS_DIR=%__COPYTERM_DATA_DIR%\sessions"
set "__COPYTERM_BIN_DIR=%__COPYTERM_DATA_DIR%\bin"

if not exist "%__COPYTERM_SESSIONS_DIR%" (
    mkdir "%__COPYTERM_SESSIONS_DIR%" >nul 2>&1
)

:: 1. Check Python Core in same directory as this script (%~dp0)
if exist "%~dp0copyterm.py" (
    python "%~dp0copyterm.py" %*
    exit /b %ERRORLEVEL%
)

:: 2. Check ~/.copyterm/bin/copyterm.py
if exist "%__COPYTERM_BIN_DIR%\copyterm.py" (
    python "%__COPYTERM_BIN_DIR%\copyterm.py" %*
    exit /b %ERRORLEVEL%
)

:: 3. Check ~/.copyterm/bin/cpt.exe
if exist "%__COPYTERM_BIN_DIR%\cpt.exe" (
    "%__COPYTERM_BIN_DIR%\cpt.exe" %*
    exit /b %ERRORLEVEL%
)

:: 4. Check location relative to script directory (%~dp0)
if exist "%~dp0..\..\src\copyterm.py" (
    python "%~dp0..\..\src\copyterm.py" %*
    exit /b %ERRORLEVEL%
)

:: 5. Fallback to python module or cpt.exe
python -m copyterm %* 2>nul || cpt.exe %*
