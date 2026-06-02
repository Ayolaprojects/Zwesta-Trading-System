@echo off
setlocal

set BACKEND_DIR=C:\backend
set STARTER=%BACKEND_DIR%\start_zwesta_backend.ps1

if not exist "%STARTER%" (
    echo ERROR: %STARTER% was not found.
    exit /b 1
)

pwsh -ExecutionPolicy Bypass -File "%STARTER%"
if errorlevel 1 exit /b %errorlevel%

exit /b 0