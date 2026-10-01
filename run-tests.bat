@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src;%~dp0tests
python -m unittest discover -s tests %*
