# ═══════════════════════════════════════════════════════════════════════════
# RESTART VPS BACKEND - Deploy SHIBUSDT Fix
# ═══════════════════════════════════════════════════════════════════════════
# RUN THIS ON YOUR VPS (38.247.146.198) via RDP
# Updates code from GitHub and restarts backend with fix
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  VPS BACKEND RESTART - SHIBUSDT FIX DEPLOYMENT" -ForegroundColor Cyan  
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Cyan

# ── STEP 1: Pull Latest Code ─────────────────────────────────────────────────
Write-Host "[1/5] Pulling latest code from GitHub..." -ForegroundColor Yellow
cd "C:\zwesta-trader\Zwesta Flutter App"
git pull origin main

$latestCommit = git log --oneline -1
Write-Host "✓ Latest commit: $latestCommit" -ForegroundColor Green

if ($latestCommit -notmatch "44e00a9") {
    Write-Host "`n⚠️  WARNING: SHIBUSDT fix commit (44e00a9) not found!" -ForegroundColor Red
    Write-Host "    The fix may not have been pulled. Continue anyway? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne 'Y') {
        Write-Host "Deployment cancelled." -ForegroundColor Red
        exit 1
    }
}

# ── STEP 2: Find Old Backend Process ─────────────────────────────────────────
Write-Host "`n[2/5] Finding running backend process..." -ForegroundColor Yellow
$proc = Get-WmiObject Win32_Process | Where-Object {
    $_.CommandLine -like "*multi_broker_backend*"
}

if ($proc) {
    Write-Host "✓ Found backend PID $($proc.ProcessId)" -ForegroundColor Green
    $oldPID = $proc.ProcessId
} else {
    Write-Host "⚠️  No backend process found by name, checking port 9000..." -ForegroundColor Yellow
    $portProc = netstat -ano | Select-String ":9000 " | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Select-Object -First 1
    
    if ($portProc -and $portProc -match '^\d+$') {
        Write-Host "✓ Found process on port 9000: PID $portProc" -ForegroundColor Green
        $oldPID = $portProc
    } else {
        Write-Host "⚠️  No backend running. Will start fresh." -ForegroundColor Yellow
        $oldPID = $null
    }
}

# ── STEP 3: Stop Old Backend ─────────────────────────────────────────────────
if ($oldPID) {
    Write-Host "`n[3/5] Stopping old backend (PID $oldPID)..." -ForegroundColor Yellow
    Stop-Process -Id $oldPID -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    Write-Host "✓ Old backend stopped" -ForegroundColor Green
} else {
    Write-Host "`n[3/5] No old backend to stop" -ForegroundColor Yellow
}

# ── STEP 4: Verify Updated Code ──────────────────────────────────────────────
Write-Host "`n[4/5] Verifying SHIBUSDT removed from code..." -ForegroundColor Yellow
$shibFound = Select-String -Path "multi_broker_backend_updated.py" -Pattern "'SHIBUSDT'" -SimpleMatch

if ($shibFound) {
    Write-Host "⚠️  WARNING: SHIBUSDT still found in code!" -ForegroundColor Red
    Write-Host "    Matches: $($shibFound.Count)" -ForegroundColor Red
    Write-Host "    Lines: $($shibFound.LineNumber -join ', ')" -ForegroundColor Red
    Write-Host "`n    This means the fix was not applied. Continue anyway? (Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -ne 'Y') {
        Write-Host "Deployment cancelled." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ SHIBUSDT successfully removed from code" -ForegroundColor Green
}

# ── STEP 5: Start New Backend ────────────────────────────────────────────────
Write-Host "`n[5/5] Starting backend with updated code..." -ForegroundColor Yellow
Start-Process python -ArgumentList "C:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py" -WindowStyle Minimized

Write-Host "✓ Backend started (process launched in background)" -ForegroundColor Green
Write-Host "  Waiting 8 seconds for startup..." -ForegroundColor Cyan
Start-Sleep -Seconds 8

# ── STEP 6: Verify Backend Health ────────────────────────────────────────────
Write-Host "`n[6/6] Testing backend health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:9000/api/health" -TimeoutSec 10
    Write-Host "✓ Backend is ONLINE" -ForegroundColor Green
    Write-Host "  Status: $($health.status)" -ForegroundColor Cyan
    Write-Host "  Database: $($health.database)" -ForegroundColor Cyan
    Write-Host "  Version: $($health.version)" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  Backend not responding yet: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Wait 15-30 seconds and check manually:" -ForegroundColor Yellow
    Write-Host "    Invoke-RestMethod -Uri http://localhost:9000/api/health" -ForegroundColor White
}

# ── FINAL STATUS ──────────────────────────────────────────────────────────────
Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✅ VPS BACKEND UPDATE COMPLETE" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Green

Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Open your mobile app and refresh" -ForegroundColor White
Write-Host "2. Bot should no longer attempt SHIBUSDT trades" -ForegroundColor White
Write-Host "3. Monitor for new errors (if any)" -ForegroundColor White
Write-Host "4. Consider stopping the losing bot ($443 loss)" -ForegroundColor White
Write-Host "`n"

Write-Host "Mobile App should connect to: http://38.247.146.198:9000" -ForegroundColor Cyan
Write-Host "Bot ID: bot_1779229018996" -ForegroundColor Cyan
Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
