@echo off
REM Setup script to create Windows Task Scheduler task for backend monitoring
REM Run this as Administrator to set up auto-restart

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Zwesta Backend - Task Scheduler Setup
echo ========================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script must run as Administrator
    echo Please run Command Prompt as Administrator and try again
    pause
    exit /b 1
)

set BACKEND_DIR=C:\backend
set START_SCRIPT=start_zwesta_backend.ps1
set TASK_NAME=ZwestaBackendAutoRestart

echo Creating task to auto-start backend...
echo.

REM Delete existing task if it exists
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Validate start script
if not exist "%BACKEND_DIR%\%START_SCRIPT%" (
    echo ERROR: %BACKEND_DIR%\%START_SCRIPT% was not found.
    echo Deploy start_zwesta_backend.ps1 before creating the scheduled task.
    pause
    exit /b 1
)

REM Create task that starts the single-instance backend launcher on boot.
echo Creating scheduled task "%TASK_NAME%"...
schtasks /create /tn "%TASK_NAME%" /tr "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%BACKEND_DIR%\%START_SCRIPT%\"" /sc onstart /rl highest /f

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Task created successfully!
    echo.
    echo Task Details:
    echo - Name: %TASK_NAME%
    echo - Trigger: At system startup
    echo - Action: Start single-instance backend launcher
    echo - Privilege: Highest ^(Admin^)
    echo.
    echo The backend launcher will now start automatically when Windows boots,
    echo ensure PostgreSQL is running, clean duplicate backend processes, and then
    echo hand off to the watchdog when needed.
    echo.
) else (
    echo.
    echo ERROR: Failed to create task
    echo Please check Task Scheduler manually
    echo.
)

pause