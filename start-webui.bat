@echo off
cd /d "%~dp0"
start "" http://127.0.0.1:8765
if exist "recorder-core\.venv\Scripts\python.exe" (
  "recorder-core\.venv\Scripts\python.exe" -m webui.server
) else (
  python -m webui.server
)
if errorlevel 1 pause
