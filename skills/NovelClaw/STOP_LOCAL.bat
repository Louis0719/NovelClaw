@echo off
setlocal
cd /d "%~dp0"

echo Stopping local NovelClaw services...
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\stop-all-local.ps1"
echo.
pause
