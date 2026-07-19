@echo off
cd /d "%~dp0"
if exist "recorder-core\.venv\Scripts\python.exe" (
  "recorder-core\.venv\Scripts\python.exe" gui.py
  goto :done
)
python gui.py
:done
if errorlevel 1 pause
