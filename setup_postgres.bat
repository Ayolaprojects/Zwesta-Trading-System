@echo off
REM PostgreSQL Setup & Backend Restart Script
REM This script configures PostgreSQL and restarts the backend

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo PostgreSQL Backend Initialization & Restart
echo ===============================================
echo.

REM Check if DATABASE_URL is set
if "%DATABASE_URL%"=="" (
    echo WARNING: DATABASE_URL environment variable is not set!
    echo.
    echo To use PostgreSQL, set DATABASE_URL like this:
    echo   set DATABASE_URL=postgresql://user:password@localhost:5432/zwesta_trader
    echo.
    echo Or for connection string format:
    echo   set DATABASE_URL=postgres://user:password@host:port/database
    echo.
    echo Falling back to SQLite mode...
    echo.
) else (
    echo DATABASE_URL is configured:
    echo   %DATABASE_URL%
    echo.
)

REM Activate Python environment
echo Activating Python environment...
call c:\zwesta-trader\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate Python environment
    exit /b 1
)

REM Run database setup
echo.
echo Running database initialization...
cd /d c:\zwesta-trader

python -c "from multi_broker_backend_updated import init_database; init_database(); print('✅ Database initialized')" 2>&1

if errorlevel 1 (
    echo ERROR: Database initialization failed
    exit /b 1
)

REM Run PostgreSQL verification test
echo.
echo Running PostgreSQL verification tests...
python c:\zwesta-trader\_test_postgres_setup.py

if errorlevel 1 (
    echo WARNING: Some verification tests failed
    echo         This may not prevent bot execution
)

echo.
echo ===============================================
echo Setup Complete!
echo ===============================================
echo.
echo To start the backend service, run:
echo   python multi_broker_backend_updated.py
echo.
echo Or from setup_auto_restart.bat:
echo   call setup_auto_restart.bat
echo.

endlocal
