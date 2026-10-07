@echo off
cd /d "%~dp0"
if not exist "desktop-ui\dist\index.html" (
  echo React UI is not built. Run: npm ci --prefix desktop-ui
  echo Then run: npm run build --prefix desktop-ui
  pause
  exit /b 1
)
if not defined LIVE_RECORDER_PORT set "LIVE_RECORDER_PORT=8765"
if exist "recorder-core\.venv\Scripts\python.exe" (
  "recorder-core\.venv\Scripts\python.exe" -m webui.server
) else (
  python -m webui.server
)
if errorlevel 1 pause
