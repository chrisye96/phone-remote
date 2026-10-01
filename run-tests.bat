@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src;%~dp0tests
if exist ".venv\Scripts\python.exe" (set PY=".venv\Scripts\python.exe") else (set PY=python)
%PY% -m unittest discover -s tests %*
