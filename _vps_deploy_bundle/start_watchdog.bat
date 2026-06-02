@echo off
REM Zwesta Backend Watchdog Launcher
REM Run this from Task Scheduler or on VPS startup.
REM It keeps the backend alive and restarts it when unhealthy.

set BACKEND_DIR=C:\backend
cd /d "%BACKEND_DIR%"

echo Checking PostgreSQL service...
set "PS_EXE=powershell"
where pwsh >nul 2>&1 && set "PS_EXE=pwsh"
"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -Command "$names = @('postgresql-x64-18','postgresql-x64-17'); $services = Get-Service -Name $names -ErrorAction SilentlyContinue; if (-not $services) { Write-Error 'No PostgreSQL Windows service found.'; exit 1 }; $svc = $services | Where-Object { $_.Status -eq 'Running' } | Select-Object -First 1; if (-not $svc) { foreach ($serviceName in $names) { $candidate = $services | Where-Object { $_.Name -eq $serviceName } | Select-Object -First 1; if ($candidate) { $svc = $candidate; break } } }; if (-not $svc) { $svc = $services | Select-Object -First 1 }; if ($svc.Status -ne 'Running') { Start-Service -Name $svc.Name; Start-Sleep -Seconds 3; $svc = Get-Service -Name $svc.Name }; if ($svc.Status -ne 'Running') { Write-Error ('PostgreSQL service failed to start: ' + $svc.Name); exit 1 }; Write-Host ('PostgreSQL service ready: ' + $svc.Name)"
if errorlevel 1 exit /b 1

set WATCHDOG_SECRET=zwesta-watchdog-2026
set WATCHDOG_BACKEND_URL=http://127.0.0.1:9000
set WATCHDOG_CHECK_INTERVAL=30
set WATCHDOG_FAIL_THRESHOLD=3
set WATCHDOG_RESPONSE_TIMEOUT=10
set WATCHDOG_MAX_MEMORY_MB=2048
set WATCHDOG_MAX_LATENCY_MS=8000
set WATCHDOG_STARTUP_WAIT=60
set WATCHDOG_SCRIPT=C:\backend\multi_broker_backend_updated.py
set AUTO_RESTART_BOTS_ON_STARTUP=true
set WATCHDOG_PYTHON=c:\zwesta-trader\.venv\Scripts\python.exe

echo Starting Zwesta Watchdog...
"%WATCHDOG_PYTHON%" "C:\backend\watchdog.py"