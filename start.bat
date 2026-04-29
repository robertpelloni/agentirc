@echo off
setlocal

:: AgentIRC Launcher
echo ========================================
echo   #agentirc  v1.1.0
echo   AutoGen Network - IRC Chat Sim
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

:: Ensure .env exists with JWT secret
if not exist .env (
    echo [SETUP] Generating JWT secret...
    for /f "delims=" %%s in ('python -c "import secrets; print(secrets.token_urlsafe(32))"') do set JWT_SECRET=%%s
    (
        echo # AgentIRC Environment Variables
        echo CHAINLIT_AUTH_SECRET=%JWT_SECRET%
        echo.
        echo # Add your API keys below:
        echo # OPENROUTER_API_KEY=sk-or-v1-...
    ) > .env
    echo [SETUP] Created .env with JWT secret.
    echo [SETUP] Edit .env to add your OPENROUTER_API_KEY if needed.
    echo.
)

:: Check if OPENROUTER_API_KEY is set (in env or .env)
python -c "from dotenv import load_dotenv; import os; load_dotenv(); assert os.environ.get('OPENROUTER_API_KEY'), 'Missing OPENROUTER_API_KEY'" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] OPENROUTER_API_KEY not set. Free-tier models will not work.
    echo [WARNING] Add it to .env:  OPENROUTER_API_KEY=sk-or-v1-...
    echo.
)

:: Install deps if needed
python -c "import chainlit" 2>nul
if %errorlevel% neq 0 (
    echo [SETUP] Installing dependencies...
    pip install -r requirements.txt
    echo.
)

:: Run
echo [INFO] Starting #agentirc on http://localhost:8000 ...
echo.
python run.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %errorlevel%.
    pause
)

endlocal
