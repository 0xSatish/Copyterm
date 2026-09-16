@echo off
:: ==============================================================================
:: COPYTERM — CMD cls Command Interceptor (Epoch Boundary Marker)
:: ==============================================================================
if not "%COPYTERM_SESSION_ID%"=="" (
    if exist "%USERPROFILE%\.copyterm\bin\copyterm.py" (
        python "%USERPROFILE%\.copyterm\bin\copyterm.py" --epoch-advance "%COPYTERM_SESSION_ID%" cls >nul 2>&1
    ) else if exist "%~dp0..\..\src\copyterm.py" (
        python "%~dp0..\..\src\copyterm.py" --epoch-advance "%COPYTERM_SESSION_ID%" cls >nul 2>&1
    )
)
cls
