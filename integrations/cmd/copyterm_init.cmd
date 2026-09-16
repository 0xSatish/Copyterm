@echo off
:: ==============================================================================
:: COPYTERM — CMD Initialization Hook (Safe, Zero-Subprocess)
:: ==============================================================================

:: Prevent re-initialization if already inside a copyterm session
if not "%COPYTERM_SESSION_ID%"=="" goto :setup_doskey

:: Pure-batch random session generation with 0 subprocess spawns (no cmd.exe recursion)
set "COPYTERM_SESSION_ID=sess_cmd_%RANDOM%_%RANDOM%"

:setup_doskey
doskey clear=cls
