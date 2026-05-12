@echo off
REM ============================================================================
REM Zwesta Trading System - Quick Start for Web + Mobile Development
REM ============================================================================
REM This script starts:
REM   1. Intelligent Backend (Port 9000)
REM   2. Flutter Web Frontend (Port 3001)
REM   3. Android Emulator (if available)
REM ============================================================================

cd /d "%~dp0"
set "FLUTTER_BIN=C:\tools\flutter\bin\flutter.bat"

if not exist "%FLUTTER_BIN%" (
  echo ERROR: Flutter SDK not found at %FLUTTER_BIN%
  exit /b 1
)

echo.
echo ================================================================================
echo   Zwesta Trading System - DEVELOPMENT QUICK START
echo ================================================================================
echo.
echo This will start:
echo   ^> Backend API on port 9000 (intelligent features)
echo   ^> Flutter Web on port 3001
echo   ^> Instructions for Android mobile app
echo.

REM Check if running as Administrator (optional)
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Not running as Administrator
    echo Some features may be limited
)

echo.
echo [Step 1] Killing any previous processes...
taskkill /F /IM python.exe 2>NUL
taskkill /F /IM dart.exe 2>NUL
taskkill /F /IM chrome.exe 2>NUL
timeout /t 2 /nobreak >NUL

echo [Step 1] OK - All cleaned up
echo.

REM ============================================================================
REM Backend
REM ============================================================================
echo [Step 2] Starting Backend on Port 9000...
echo.
start "Zwesta Backend (Port 9000)" /d "%~dp0" python multi_broker_backend_updated.py
echo [Step 2] OK - Backend starting in background...
timeout /t 5 /nobreak >NUL

REM ============================================================================
REM Web Frontend
REM ============================================================================
echo.
echo [Step 3] Starting Flutter Web on Port 3001...
echo.
start "Zwesta Frontend (Port 3001)" /d "%~dp0" cmd /k "\"%FLUTTER_BIN%\" run -d chrome --web-port=3001"
echo [Step 3] OK - Web app starting in new terminal...
timeout /t 3 /nobreak >NUL

REM ============================================================================
REM Summary
REM ============================================================================
echo.
echo ================================================================================
echo   SERVICES STARTED
echo ================================================================================
echo.
echo Backend API:
echo   URL: http://localhost:9000
echo   Status: http://localhost:9000/api/bot/status
echo.
echo Web Frontend:
echo   URL: http://localhost:3001
echo   Browser should auto-open in Chrome
echo.
echo Mobile App (Android):
echo   For detailed mobile setup, see: MOBILE_APP_SETUP.md
echo   Quick start (if emulator ready):
echo   1. android-emulator.bat (separate command)
echo        OR flutter run
echo.
echo.
echo TEST CHECKLIST:
echo   [ ] Backend responding: curl http://localhost:9000/api/bot/status
echo   [ ] Web loads: http://localhost:3001
echo   [ ] Create a bot and verify it appears
echo   [ ] Check Dashboard shows real-time updates (5 sec intervals)
echo   [ ] Monitor intelligent features:
echo       - Strategy switching when performance improves
echo       - Position scaling on wins/losses
echo.
echo.
echo STOP SERVICES:
echo   Close the terminal windows, or:
echo   taskkill /F /IM python.exe
echo   taskkill /F /IM dart.exe
echo.
echo ================================================================================
echo.
echo Press any key to continue...
pause >NUL

echo.
echo Starting monitoring... (Ctrl+C to return)
echo.

REM Keep window open to monitor
echo Waiting for services startup... Checking backend health every 10 seconds.
:monitor
timeout /t 10 /nobreak >NUL
cls
echo.
echo === SYSTEM STATUS ===
echo.

REM Check backend health
powershell -Command "^
try { ^
  $result = Invoke-RestMethod http://localhost:9000/api/bot/status -ErrorAction Stop -TimeoutSec 2; ^
  Write-Host '✓ Backend ONLINE' -ForegroundColor Green; ^
  Write-Host '  Bots: ' + $result.active_bots.Count -ForegroundColor Green; ^
} catch { ^
  Write-Host '✗ Backend OFFLINE' -ForegroundColor Red; ^
}" >NUL 2>&1

if errorlevel 0 (
    echo ✓ Backend ONLINE
) else (
    echo ✗ Backend OFFLINE
)

echo.
echo ✓ Web Frontend running (check http://localhost:3001)
echo.
echo Press Ctrl+C to stop monitoring and return...
goto monitor
