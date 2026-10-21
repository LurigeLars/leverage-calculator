@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Build Leverage Calculator

echo [1/3] Checking Python...
where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python missing. Install Python 3.12 or 3.13 from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

echo [2/3] Creating virtual environment and installing build dependencies...
set "PYTHON=py -3.13"
py -3.13 --version >nul 2>nul
if errorlevel 1 (
  set "PYTHON=py -3.12"
  py -3.12 --version >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python 3.12 or 3.13 is required.
    pause
    exit /b 1
  )
)

if not exist ".venv\Scripts\python.exe" (
  %PYTHON% -m venv .venv
  if errorlevel 1 goto :failed
)
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 goto :failed

echo [3/3] Building standalone Windows application...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name LeverageCalculator --add-data "web;web" --collect-all webview --hidden-import webview.platforms.edgechromium desktop\main.py
if errorlevel 1 goto :failed

echo.
echo DONE: dist\LeverageCalculator.exe
echo You can copy the .exe anywhere. Python is not required on the target machine.
explorer "dist"
pause
exit /b 0

:failed
echo.
echo Build failed. See the error message above.
pause
exit /b 1
