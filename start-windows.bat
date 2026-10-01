@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
    pause
    exit /b 1
  )
  echo First run: installing into .venv, this takes a minute...
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install -q -e .
)
".venv\Scripts\python.exe" -m phone_remote
pause
