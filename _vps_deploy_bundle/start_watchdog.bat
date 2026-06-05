@echo off
REM Zwesta Backend Watchdog Launcher
REM Run this from Task Scheduler or on VPS startup.
REM It keeps the backend alive and restarts it when unhealthy.

set BACKEND_DIR=C:\backend
cd /d "%BACKEND_DIR%"

echo Checking PostgreSQL connectivity...
set "PS_EXE=powershell"
where pwsh >nul 2>&1 && set "PS_EXE=pwsh"
"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -Command "$names = @('postgresql-x64-18','postgresql-x64-17','postgresql'); $services = Get-Service -Name $names -ErrorAction SilentlyContinue; $svc = $null; if ($services) { $svc = $services | Where-Object { $_.Status -eq 'Running' } | Select-Object -First 1; if (-not $svc) { foreach ($serviceName in $names) { $candidate = $services | Where-Object { $_.Name -eq $serviceName } | Select-Object -First 1; if ($candidate) { $svc = $candidate; break } } } }; if ($svc -and $svc.Status -ne 'Running') { try { Start-Service -Name $svc.Name -ErrorAction Stop; Start-Sleep -Seconds 5 } catch { Write-Warning ('Could not start service via SCM: ' + $_.Exception.Message) } }; try { $tcp = New-Object System.Net.Sockets.TcpClient('127.0.0.1', 5432); $tcp.Close(); Write-Host 'PostgreSQL is accepting connections on port 5432' } catch { Write-Warning 'PostgreSQL not reachable on port 5432 - continuing anyway' }"

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

REM ==================== LAUNCH ALL 3 MT5 TERMINALS ====================
echo Launching MT5 terminals (if not already running)...
set "PS_EXE2=powershell"
where pwsh >nul 2>&1 && set "PS_EXE2=pwsh"
"%PS_EXE2%" -NoProfile -ExecutionPolicy Bypass -Command ^
  "$terminals = @(" ^
  "  'C:\MT5\Exness-Live\terminal64.exe\terminal64.exe'," ^
  "  'C:\MT5\Exness-Live\Max terminal64.exe\terminal64.exe'," ^
  "  'C:\MT5\Exness-Demo\terminal64.exe\terminal64.exe'" ^
  ");" ^
  "foreach ($t in $terminals) {" ^
  "  if (-not (Test-Path $t)) { Write-Host \"SKIP (not found): $t\"; continue }" ^
  "  $norm = [System.IO.Path]::GetFullPath($t).ToLower();" ^
  "  $running = Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.ToLower() -eq $norm -and $_.SessionId -ne 0 };" ^
  "  if ($running) { Write-Host \"Already running: $t\" } else { Start-Process $t; Write-Host \"Launched: $t\" }" ^
  "}"
echo MT5 terminal launch complete. Waiting 12s for terminals to initialise...
timeout /t 12 /nobreak >nul

REM Auto-detect Python: prefer venv, fall back to system Python
set WATCHDOG_PYTHON=
if exist "c:\zwesta-trader\.venv\Scripts\python.exe" set WATCHDOG_PYTHON=c:\zwesta-trader\.venv\Scripts\python.exe
if "%WATCHDOG_PYTHON%"=="" if exist "C:\Program Files\Python311\python.exe" set WATCHDOG_PYTHON=C:\Program Files\Python311\python.exe
if "%WATCHDOG_PYTHON%"=="" if exist "C:\Python312\python.exe" set WATCHDOG_PYTHON=C:\Python312\python.exe
if "%WATCHDOG_PYTHON%"=="" if exist "C:\Python311\python.exe" set WATCHDOG_PYTHON=C:\Python311\python.exe
if "%WATCHDOG_PYTHON%"=="" if exist "C:\Python310\python.exe" set WATCHDOG_PYTHON=C:\Python310\python.exe
if "%WATCHDOG_PYTHON%"=="" if exist "C:\Python39\python.exe" set WATCHDOG_PYTHON=C:\Python39\python.exe
if "%WATCHDOG_PYTHON%"=="" for /f "delims=" %%i in ('where python 2^>nul') do if "%WATCHDOG_PYTHON%"=="" set WATCHDOG_PYTHON=%%i
if "%WATCHDOG_PYTHON%"=="" (
    echo ERROR: Could not find python.exe - set WATCHDOG_PYTHON manually in this file
    exit /b 1
)
echo Using Python: %WATCHDOG_PYTHON%

echo Starting Zwesta Watchdog...
"%WATCHDOG_PYTHON%" "C:\backend\watchdog.py"
