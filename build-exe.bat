@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=recorder-core\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

call npm.cmd ci --prefix desktop-ui
if errorlevel 1 (
  echo Failed to install React UI dependencies.
  pause
  exit /b 1
)
call npm.cmd run build --prefix desktop-ui
if errorlevel 1 (
  echo Failed to build React desktop UI.
  pause
  exit /b 1
)

"%PYTHON_EXE%" -m pip install -r desktop-requirements.txt
if errorlevel 1 (
  echo Failed to install desktop WebView dependencies.
  pause
  exit /b 1
)

"%PYTHON_EXE%" -m unittest discover -s tests
if errorlevel 1 (
  echo Python tests or packaged source syntax check failed. EXE was not built.
  pause
  exit /b 1
)

"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean LiveRecorder.spec
if errorlevel 1 (
  echo.
  echo Build failed. Install PyInstaller first:
  echo   "%PYTHON_EXE%" -m pip install pyinstaller
  pause
  exit /b 1
)

copy /y "README.md" "dist\LiveRecorder\README.md" >nul

echo.
echo Build completed: dist\LiveRecorder\LiveRecorder.exe
pause
