# DEPLOY UPDATED BACKEND TO VPS
# ─────────────────────────────────────────────────────────────────────────────
# RDP to 148.113.5.39, open PowerShell as Administrator, run this script.
# It will:
#   1. Find and kill the old backend process
#   2. Copy the updated backend file
#   3. Start the new backend
# ─────────────────────────────────────────────────────────────────────────────

# If running from LOCAL machine via WinRM (optional, may not be enabled):
# $s = New-PSSession -ComputerName 148.113.5.39 -Credential (Get-Credential)
# Invoke-Command -Session $s -ScriptBlock { ... }

# ── STEP 1: Find backend process ──────────────────────────────────────────────
Write-Host "Finding backend process..." -ForegroundColor Cyan
$proc = Get-WmiObject Win32_Process | Where-Object {
    $_.CommandLine -like "*multi_broker_backend*" -or
    $_.CommandLine -like "*backend_updated*"
}
if ($proc) {
    Write-Host "Found process PID $($proc.ProcessId): $($proc.CommandLine.Substring(0, [Math]::Min(80, $proc.CommandLine.Length)))"
} else {
    Write-Host "No backend process found by name, checking port 9000..."
    $netstat = netstat -ano | Select-String ":9000 "
    Write-Host $netstat
}

# ── STEP 2: Stop the old backend ─────────────────────────────────────────────
Write-Host "`nStopping old backend..." -ForegroundColor Yellow
if ($proc) {
    Stop-Process -Id $proc.ProcessId -Force
    Write-Host "Killed PID $($proc.ProcessId)"
} else {
    # Kill by port
    $portProc = netstat -ano | Select-String ":9000 " | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Select-Object -First 1
    if ($portProc -and $portProc -match '^\d+$') {
        Stop-Process -Id $portProc -Force
        Write-Host "Killed PID $portProc (was listening on :9000)"
    }
}
Start-Sleep -Seconds 3

# ── STEP 3: Backup old file ───────────────────────────────────────────────────
Write-Host "`nBacking up old backend file..." -ForegroundColor Cyan
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "C:\backend\multi_broker_backend_updated.py" "C:\backend\multi_broker_backend_updated.BACKUP_$ts.py"
Write-Host "Backup saved as: multi_broker_backend_updated.BACKUP_$ts.py"

# ── STEP 4: The new file should already be at C:\backend\multi_broker_backend_updated.py
#    (you copied it via RDP file transfer / drag-drop)
#    Verify syntax first:
Write-Host "`nVerifying syntax of new backend file..." -ForegroundColor Cyan
python -c "import ast; ast.parse(open('C:/backend/multi_broker_backend_updated.py','r',encoding='utf-8',errors='replace').read()); print('SYNTAX OK')"

Write-Host "`nEnsuring waitress is installed for production startup..." -ForegroundColor Cyan
python -c "import waitress; print('WAITRESS OK')" 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip install waitress
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install waitress"
    }
}

# ── STEP 5: Start new backend ─────────────────────────────────────────────────
Write-Host "`nStarting new backend..." -ForegroundColor Green
Start-Process -FilePath "python" -ArgumentList "C:\backend\multi_broker_backend_updated.py" -WindowStyle Minimized
Start-Sleep -Seconds 5

# ── STEP 6: Verify it's running ───────────────────────────────────────────────
Write-Host "`nVerifying backend started..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri "http://localhost:9000/api/user/login" -Method POST `
        -Body '{"email":"zwexman@gmail.com","password":"Zwesta1985"}' `
        -ContentType "application/json" -TimeoutSec 15
    Write-Host "Backend OK: $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Backend not responding yet: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Wait 15s and try again or check python process..."
}

Write-Host "`n✅ Done. Backend should be running on port 9000." -ForegroundColor Green
