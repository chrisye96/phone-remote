@echo off
cd /d "%~dp0"
where python >/dev/null 2>nul
if errorlevel 1 (
  echo Python not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
set PYTHONPATH=%~dp0src
python -m phone_remote
pause
