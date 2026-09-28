@echo off
setlocal
cd /d "%~dp0"
echo Resetting NLAMS central demo state...
if exist "integration\nlams_integration.db" del /q "integration\nlams_integration.db"
echo Central workflow database reset. Start START_ALL_NLAMS.bat to reseed NH44-MH-001 / P-001.
pause
endlocal
