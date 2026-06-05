<#
.SYNOPSIS
    One-shot deploy script that applies the 2026-06-04 bot fixes on the VPS.

.DESCRIPTION
    Run this on the VPS (in an elevated PowerShell, from C:\backend) to fix:
      1. Binance worker-pool crash storm  -> sets BINANCE_WORKER_COUNT=0 in .env
         so Binance bots run as in-process threads (like MT5 single-process mode)
         instead of spawning heavyweight worker processes that re-import the whole
         backend and get killed/respawned forever (CPU saturation -> bots never
         display, never trade).
      2. Stale account-profit-staircase / equity watermark that blocks live entries
         with "account profit staircase floor active ... (surge guard)" -> clears
         the phantom peak so bots re-baseline at real equity.

    Steps performed:
      - Back up .env
      - Patch BINANCE_WORKER_COUNT -> 0
      - Stop watchdog + backend + any stray binance_worker.py processes
      - Run _reset_profit_staircase.py --apply against the live database
      - Restart the backend via start_zwesta_backend.ps1
      - Verify /api/health

.PARAMETER SkipStaircaseReset
    Only apply the worker-pool .env fix and restart; do not touch bot state.

.PARAMETER WhatIfReset
    Run the staircase reset in DRY-RUN mode (show changes, write nothing).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\backend\apply_bot_fixes.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File C:\backend\apply_bot_fixes.ps1 -WhatIfReset
#>

param(
    [switch]$SkipStaircaseReset,
    [switch]$WhatIfReset
)

$ErrorActionPreference = 'Stop'
$backendDir = 'C:\backend'
$envFile = Join-Path $backendDir '.env'
$resetScript = Join-Path $backendDir '_reset_profit_staircase.py'
$startScript = Join-Path $backendDir 'start_zwesta_backend.ps1'
$healthUrl = 'http://127.0.0.1:9000/api/health'

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }

Set-Location $backendDir

# ---------------------------------------------------------------------------
# 0. Resolve python
# ---------------------------------------------------------------------------
$pythonExe = $null
foreach ($candidate in @('c:\zwesta-trader\.venv\Scripts\python.exe', 'C:\Python313\python.exe', 'C:\Python312\python.exe', 'C:\Python311\python.exe')) {
    if (Test-Path $candidate) { $pythonExe = $candidate; break }
}
if (-not $pythonExe) {
    try { $pythonExe = (Get-Command python -ErrorAction Stop | Select-Object -First 1).Source } catch {}
}
if (-not $pythonExe) { throw 'Could not find a python executable.' }
Write-Host "Using python: $pythonExe" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
# 1. Patch .env -> BINANCE_WORKER_COUNT=0
# ---------------------------------------------------------------------------
Write-Step 'Patching .env (BINANCE_WORKER_COUNT=0)'
if (-not (Test-Path $envFile)) { throw "Missing .env at $envFile" }

$backup = "$envFile.bak_$(Get-Date -Format yyyyMMdd_HHmmss)"
Copy-Item $envFile $backup -Force
Write-Host "Backed up .env -> $backup" -ForegroundColor DarkGray

$envLines = Get-Content $envFile
$found = $false
$envLines = $envLines | ForEach-Object {
    if ($_ -match '^\s*BINANCE_WORKER_COUNT\s*=') {
        $found = $true
        if ($_ -match '=\s*0\s*$') { Write-Host 'BINANCE_WORKER_COUNT already 0' -ForegroundColor Green }
        else { Write-Host "Changing '$_' -> 'BINANCE_WORKER_COUNT=0'" -ForegroundColor Yellow }
        'BINANCE_WORKER_COUNT=0'
    } else { $_ }
}
if (-not $found) {
    Write-Host 'BINANCE_WORKER_COUNT not found; appending it.' -ForegroundColor Yellow
    $envLines += 'BINANCE_WORKER_COUNT=0'
}
Set-Content -Path $envFile -Value $envLines -Encoding ASCII

# ---------------------------------------------------------------------------
# 2. Stop watchdog + backend + stray binance workers
# ---------------------------------------------------------------------------
Write-Step 'Stopping watchdog, backend, and stray binance_worker.py processes'

function Stop-ByCommandFragment($fragment) {
    $procs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^python(w)?\.exe$' -and $_.CommandLine -like "*$fragment*" })
    foreach ($p in $procs) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            Write-Host "  stopped PID $($p.ProcessId) ($fragment)" -ForegroundColor DarkGray
        } catch {
            Write-Warning "  could not stop PID $($p.ProcessId): $($_.Exception.Message)"
        }
    }
}

Stop-ByCommandFragment 'watchdog.py'
Stop-ByCommandFragment 'binance_worker.py'
Stop-ByCommandFragment 'multi_broker_backend_updated.py'
Start-Sleep -Seconds 3

# Belt-and-braces: kill any remaining binance_worker via taskkill tree
$leftover = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^python(w)?\.exe$' -and $_.CommandLine -like '*binance_worker.py*' })
foreach ($p in $leftover) {
    & taskkill /PID $p.ProcessId /T /F 2>$null | Out-Null
}

# ---------------------------------------------------------------------------
# 3. Reset stale profit-staircase / watermark state
# ---------------------------------------------------------------------------
if ($SkipStaircaseReset) {
    Write-Step 'Skipping staircase reset (-SkipStaircaseReset)'
} else {
    if (-not (Test-Path $resetScript)) { throw "Missing reset script: $resetScript" }
    if ($WhatIfReset) {
        Write-Step 'Staircase reset (DRY RUN)'
        & $pythonExe $resetScript
    } else {
        Write-Step 'Staircase reset (APPLY)'
        & $pythonExe $resetScript --apply
    }
    if ($LASTEXITCODE -ne 0) { throw "Reset script exited with code $LASTEXITCODE" }
}

# ---------------------------------------------------------------------------
# 4. Restart backend
# ---------------------------------------------------------------------------
Write-Step 'Restarting backend via start_zwesta_backend.ps1'
if (-not (Test-Path $startScript)) { throw "Missing start script: $startScript" }
& powershell -ExecutionPolicy Bypass -File $startScript

# ---------------------------------------------------------------------------
# 5. Verify health
# ---------------------------------------------------------------------------
Write-Step 'Verifying backend health'
$ok = $false
for ($i = 1; $i -le 18; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5
        if ($resp.status -eq 'ok') { $ok = $true; break }
    } catch {}
    Start-Sleep -Seconds 5
}

if ($ok) {
    Write-Host "`nSUCCESS: backend healthy on $healthUrl" -ForegroundColor Green
    Write-Host 'Confirm in the backend log that you now see:' -ForegroundColor Green
    Write-Host '  [OK] Binance worker pool disabled (BINANCE_WORKER_COUNT=0) - using local Binance threads' -ForegroundColor Green
    Write-Host 'and that "Binance worker N started (PID ...)" lines have STOPPED.' -ForegroundColor Green
} else {
    Write-Warning "Backend did not report healthy within the wait window. Check the backend console / log."
    exit 1
}
