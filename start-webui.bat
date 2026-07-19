@echo off
cd /d "%~dp0"
start "" http://127.0.0.1:8765
if exist "recorder-core\.venv\Scripts\python.exe" (
  "recorder-core\.venv\Scripts\python.exe" webui\server.py
) else (
  python webui\server.py
)
if errorlevel 1 pause
