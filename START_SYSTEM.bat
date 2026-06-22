@echo off
REM ============================================================================
REM Zwesta Trading System - PostgreSQL Backend + Flutter App Start
REM ============================================================================
REM This script starts the backend and prepares for Flutter app connection
REM ============================================================================

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo.
echo ================================================================================
echo   Zwesta Trading System - PostgreSQL Backend + Flutter App
echo ================================================================================
echo.

REM Step 1: Verify PostgreSQL is accessible
echo [Step 1] Verifying PostgreSQL connection...
"C:\zwesta-trader\.venv\Scripts\python.exe" -c "import psycopg2; psycopg2.connect('postgresql://zwesta_admin:Zwesta%%40Trading2026%%21@localhost:5432/zwesta_trading'); print('OK - PostgreSQL connected')" 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL connection failed.
    echo         Please ensure PostgreSQL is running on port 5432.
    echo         Database: zwesta_trading, User: zwesta_admin
    pause
    exit /b 1
)

REM Step 2: Start backend (if not already running)
echo [Step 2] Starting backend (PostgreSQL mode)...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Zwesta*" 2>NUL | find /I "python.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Backend already running
) else (
    start "Zwesta PostgreSQL Backend (Port 9000)" /B ""C:\zwesta-trader\.venv\Scripts\python.exe" "multi_broker_backend_updated.py"
    timeout /t 5 /nobreak >NUL
)

REM Step 3: Verify backend health
echo [Step 3] Verifying backend health...
curl -s http://localhost:9000/api/health >NUL 2>&1
if errorlevel 1 (
    echo ERROR: Backend not responding on port 9000
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