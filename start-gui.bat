@echo off
cd /d "%~dp0"
if exist "recorder-core\.venv\Scripts\python.exe" (
  "recorder-core\.venv\Scripts\python.exe" launcher.py --desktop
  goto :done
)
python launcher.py --desktop
:done
if errorlevel 1 pause
