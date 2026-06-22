@echo off
REM ============================================================================
REM Zwesta Trading System - PostgreSQL Backend + Flutter App Start
REM ============================================================================

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo.
echo ================================================================================
echo   Zwesta Trading System - PostgreSQL Backend + Flutter App
echo ================================================================================
echo.

echo [Step 1] Verifying PostgreSQL connection...
"C:\zwesta-trader\.venv\Scripts\python.exe" -c "import psycopg2; psycopg2.connect('postgresql://zwesta_admin:Zwesta%%40Trading2026%%21@localhost:5432/zwesta_trading'); print('OK PostgreSQL connected')" 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL connection failed. Please ensure PostgreSQL is running.
    echo         The database 'zwesta_trading' must exist with user 'zwesta_admin'.
    echo Run: createdb -U postgres zwesta_trading
    pause
    exit /b 1
)

echo [Step 2] Starting backend with PostgreSQL mode...
"C:\zwesta-trader\.venv\Scripts\python.exe" "multi_broker_backend_updated.py"
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