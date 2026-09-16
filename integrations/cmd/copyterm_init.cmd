@echo off
:: ==============================================================================
:: COPYTERM — CMD AutoRun Initialization Hook
:: Ensures automatic per-terminal capture session creation on CMD startup
:: ==============================================================================

:: Prevent re-initialization if already inside a copyterm session
if not "%COPYTERM_SESSION_ID%"=="" goto :setup_doskey

set "__CPT_DATA_DIR=%USERPROFILE%\.copyterm"
set "__CPT_BIN_DIR=%__CPT_DATA_DIR%\bin"

:: 1. Initialize session via python core or cpt binary
if exist "%__CPT_BIN_DIR%\copyterm.py" (
    for /f "usebackq tokens=*" %%i in (`python "%__CPT_BIN_DIR%\copyterm.py" --init-session cmd 2^>nul`) do (
        set "COPYTERM_SESSION_ID=%%i"
    )
) else if exist "%~dp0..\..\src\copyterm.py" (
    for /f "usebackq tokens=*" %%i in (`python "%~dp0..\..\src\copyterm.py" --init-session cmd 2^>nul`) do (
        set "COPYTERM_SESSION_ID=%%i"
    )
)

:: 2. Fallback session generation if runtime output was empty
if "%COPYTERM_SESSION_ID%"=="" (
    set "COPYTERM_SESSION_ID=sess_%RANDOM%_%RANDOM%"
)

:setup_doskey
:: 3. Setup doskey aliases for epoch clear boundary and canonical commands
doskey clear=cls
