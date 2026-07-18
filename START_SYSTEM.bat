@echo off
REM ============================================================================
REM Zwesta Trading System - PostgreSQL Backend + Flutter App Start
REM ============================================================================
REM This script starts the backend and prepares for Flutter app connection
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

REM Step 1: Verify PostgreSQL is accessible
echo [Step 1] Verifying PostgreSQL connection...
"%PYTHON_EXE%" -c "import os, urllib.parse, psycopg2, dotenv; dotenv.load_dotenv('.env', override=True); db=os.getenv('DATABASE_URL','').strip(); db=db or ('postgresql://' + os.getenv('POSTGRES_USER','zwesta_admin') + ':' + urllib.parse.quote(os.getenv('POSTGRES_PASSWORD','')) + '@' + os.getenv('POSTGRES_HOST','127.0.0.1') + ':' + os.getenv('POSTGRES_PORT','5432') + '/' + os.getenv('POSTGRES_DB','zwesta_trading')); psycopg2.connect(db); print('OK - PostgreSQL connected')" 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL connection failed.
    echo         Please ensure PostgreSQL is running on port 5432.
    echo         Check .env values: POSTGRES_HOST/PORT/DB/USER/PASSWORD or DATABASE_URL.
    pause
    exit /b 1
)

REM Step 2: Start backend (if not already running)
echo [Step 2] Starting backend (PostgreSQL mode)...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Zwesta*" 2>NUL | find /I "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Backend already running
) else (
    start "Zwesta PostgreSQL Backend (Port 9000)" /B "%PYTHON_EXE%" "multi_broker_backend_updated.py"
)

REM Step 3: Verify backend health
echo [Step 3] Verifying backend health...
set /a HEALTH_OK=0
for /L %%I in (1,1,60) do (
    "%PYTHON_EXE%" -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:9000/api/health', timeout=3); sys.exit(0)" >NUL 2>&1
    if not errorlevel 1 (
        set /a HEALTH_OK=1
        goto :health_ready
    )
    timeout /t 1 /nobreak >NUL
)

:health_ready
if "%HEALTH_OK%"=="0" (
    echo ERROR: Backend not responding on port 9000 after 60 seconds
    echo        Check backend logs above for startup errors.
    pause
    exit /b 1
)
echo OK - Backend healthy

echo.
echo ================================================================================
echo   SYSTEM READY
echo ================================================================================
echo.
echo Backend API:    http://localhost:9000
echo Test Login:     testuser@example.com / TestPass123!
echo Health Check:   http://localhost:9000/api/health
echo.
echo To run Flutter app:
echo   flutter pub get
echo   flutter run -d chrome --web-port=3001
echo   OR flutter run -d android
echo.
echo Press any key to stop backend...
pause >NUL

REM Stop backend on exit
taskkill /F /FI "WINDOWTITLE eq Zwesta*" 2>NUL
exit /b 0