@echo off
:: ==============================================================================
:: COPYTERM — CMD Integration Script
:: ==============================================================================

if "%COPYTERM_SESSION_ID%"=="" (
    set "COPYTERM_SESSION_ID=sess_%RANDOM%_%RANDOM%"
)

set "__COPYTERM_DATA_DIR=%USERPROFILE%\.copyterm"
set "__COPYTERM_SESSIONS_DIR=%__COPYTERM_DATA_DIR%\sessions"

if not exist "%__COPYTERM_SESSIONS_DIR%" (
    mkdir "%__COPYTERM_SESSIONS_DIR%" >nul 2>&1
)
