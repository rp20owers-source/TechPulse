@echo off
setlocal
cd /d "%~dp0"
set "TECHPULSE_RUNTIME=%LOCALAPPDATA%\TechPulse\runtime-0.1"
if defined TECHPULSE_RUNTIME_DIR set "TECHPULSE_RUNTIME=%TECHPULSE_RUNTIME_DIR%"
python -c "import sys; assert (3,12) <= sys.version_info[:2] < (3,15)" >nul 2>&1
if errorlevel 1 (
  echo TechPulse needs Python 3.12, 3.13 or 3.14. Install Python from python.org, then run again.
  pause
  exit /b 1
)
if not exist "%TECHPULSE_RUNTIME%\Scripts\python.exe" (
  python -m venv "%TECHPULSE_RUNTIME%"
  if errorlevel 1 goto setup_failed
)
"%TECHPULSE_RUNTIME%\Scripts\python.exe" -m pip install --disable-pip-version-check --require-hashes -r "%~dp0requirements.lock"
if errorlevel 1 goto setup_failed
set "PYTHONPATH=%~dp0src"
"%TECHPULSE_RUNTIME%\Scripts\python.exe" -m techpulse %*
if errorlevel 1 (
  echo TechPulse did not start successfully. Preserve your data and see docs\USER_GUIDE.md.
  pause
  exit /b 1
)
exit /b 0
:setup_failed
echo Dependency setup failed. Check Python and internet access; no financial data was downloaded.
pause
exit /b 1
