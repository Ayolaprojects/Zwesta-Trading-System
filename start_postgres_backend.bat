@echo off
REM ============================================================================
REM Zwesta Trading System - PostgreSQL Backend + Flutter App Start
REM ============================================================================

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set ZWESTA_SKIP_PYTHON_REEXEC=1
set MT5_STARTUP_WARMUP=0
if not defined PORT set PORT=9000

set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

if /I "%PYTHON_EXE%"=="python" (
    where python >NUL 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found on PATH. Install Python or create venv at venv\Scripts\python.exe
        pause
        exit /b 1
    )
)

echo.
echo ================================================================================
echo   Zwesta Trading System - PostgreSQL Backend + Flutter App
echo ================================================================================
echo.

echo [Step 1] Verifying PostgreSQL connection...
"%PYTHON_EXE%" -c "import os, urllib.parse, psycopg2, dotenv; dotenv.load_dotenv('.env', override=True); db=os.getenv('DATABASE_URL','').strip(); db=db or ('postgresql://' + os.getenv('POSTGRES_USER','zwesta_admin') + ':' + urllib.parse.quote(os.getenv('POSTGRES_PASSWORD','')) + '@' + os.getenv('POSTGRES_HOST','127.0.0.1') + ':' + os.getenv('POSTGRES_PORT','5432') + '/' + os.getenv('POSTGRES_DB','zwesta_trading')); psycopg2.connect(db); print('OK PostgreSQL connected')" 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL connection failed. Please ensure PostgreSQL is running.
    echo         Check .env values: POSTGRES_HOST/PORT/DB/USER/PASSWORD or DATABASE_URL.
    echo         If database is missing, create it with psql:
    echo         psql -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE zwesta_trading;"
    pause
    exit /b 1
)

echo [Step 2] Starting backend with PostgreSQL mode...
"%PYTHON_EXE%" "multi_broker_backend_updated.py"
if errorlevel 1 (
    echo ERROR: Backend failed to start
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   BACKEND STARTED
echo ================================================================================
echo.
echo Backend API:    http://localhost:9000
echo Health Check:   http://localhost:9000/api/health
echo Bot Status:     http://localhost:9000/api/bot/status
echo.
echo To run Flutter app:
echo   flutter run -d chrome --web-port=3001
echo   flutter run -d android
echo.
echo Press any key to stop backend...