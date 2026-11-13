@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_dev.ps1"
if errorlevel 1 pause
endlocal
