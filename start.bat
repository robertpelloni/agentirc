@echo off
setlocal enabledelayedexpansion

:: Check if Python is in PATH
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to your PATH.
    pause
    exit /b 1
)

:: Check for virtual environment
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] No virtual environment (venv) found. Running with system Python.
)

:: Check requirements
if exist requirements.txt (
    echo [INFO] Checking dependencies...
    pip install -r requirements.txt
)

echo [INFO] Starting #agentirc...
python run.py

if %errorlevel% neq 0 (
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)

endlocal
