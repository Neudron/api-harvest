@echo off
setlocal EnableDelayedExpansion

:: Check that Python is installed
where python >nul 2>&1
if errorlevel 1 (
    echo Error: python not found. Install Python 3.11 or later and re-run.
    pause
    exit /b 1
)

:: Check Python version is 3.11+
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("!PYVER!") do (
    set MAJOR=%%a
    set MINOR=%%b
)
if !MAJOR! LSS 3 (
    echo Error: Python 3.11+ is required (found !PYVER!).
    pause
    exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 11 (
    echo Error: Python 3.11+ is required (found !PYVER!).
    pause
    exit /b 1
)

:: Create venv on first run, reuse on subsequent runs
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -e . -q

echo Installing Playwright browser...
playwright install chromium

if not exist "harvest-chrome\" mkdir harvest-chrome

echo.
echo Setup complete. Starting harvest...
echo.
harvest run --profile-dir .\harvest-chrome
