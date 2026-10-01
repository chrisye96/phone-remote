@echo off
rem Build a single PhoneRemote.exe into dist\ (no Python needed to run it).
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Run start-windows.bat once first to create .venv.
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install -q pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name PhoneRemote ^
  --add-data "%CD%\src\phone_remote\web;phone_remote\web" ^
  --collect-submodules winrt --collect-submodules pystray ^
  --specpath build --workpath build --distpath dist "%CD%\scripts\entry.py"
