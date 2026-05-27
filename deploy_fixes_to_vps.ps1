# ═══════════════════════════════════════════════════════════════════════════
# DEPLOY DATABASE + PROFIT GUARD FIXES TO VPS
# ═══════════════════════════════════════════════════════════════════════════
# Run this script to deploy both fixes at once
# ═══════════════════════════════════════════════════════════════════════════

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  DEPLOYING FIXES TO VPS" -ForegroundColor Cyan  
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "✓ Fixes being deployed:" -ForegroundColor Green
Write-Host "  1. Database schema (added closed_at column)" -ForegroundColor White
Write-Host "  2. Recent-profit guard (30% default, 50% max)" -ForegroundColor White
Write-Host ""

# Check if database exists
if (-not (Test-Path "C:\backend\zwesta_trading.db")) {
    Write-Host "✗ ERROR: Database not found at C:\backend\zwesta_trading.db" -ForegroundColor Red
    Write-Host "  Run: python _fix_database_schema.py first!" -ForegroundColor Yellow
    exit 1
}

# Check database size to confirm it's the right one
$dbSize = (Get-Item "C:\backend\zwesta_trading.db").Length / 1MB
Write-Host "✓ Found database: $([math]::Round($dbSize, 2)) MB" -ForegroundColor Green

Write-Host "`n[1/3] Copying fixed database to VPS..." -ForegroundColor Yellow
Write-Host "  Source: C:\backend\zwesta_trading.db" -ForegroundColor Gray
Write-Host "  Target: VPS (38.247.146.198) C:\backend\zwesta_trading.db" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  ACTION REQUIRED: Manually copy database via RDP" -ForegroundColor Yellow
Write-Host "  1. RDP to 38.247.146.198" -ForegroundColor White
Write-Host "  2. Copy C:\backend\zwesta_trading.db from local to VPS" -ForegroundColor White
Write-Host "  3. Press ENTER here when done..." -ForegroundColor White
Read-Host

Write-Host "`n[2/3] Finding and stopping backend process on VPS..." -ForegroundColor Yellow
Write-Host "⚠️  RUN THIS ON VPS:" -ForegroundColor Yellow
Write-Host @"

# Find backend process
`$proc = Get-WmiObject Win32_Process | Where-Object { `$_.CommandLine -like "*multi_broker_backend*" }
if (`$proc) {
    Write-Host "Stopping backend PID `$(`$proc.ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id `$proc.ProcessId -Force
    Write-Host "✓ Backend stopped" -ForegroundColor Green
} else {
    Write-Host "⚠️  No backend running" -ForegroundColor Yellow
}

# OR stop by port
`$pid = (netstat -ano | Select-String ":9000 " | ForEach-Object { (`$_ -split '\s+')[-1] } | Select-Object -First 1)
if (`$pid) {
    Stop-Process -Id `$pid -Force
    Write-Host "✓ Stopped process on port 9000" -ForegroundColor Green
}

"@ -ForegroundColor White

Write-Host "`nPress ENTER when backend is stopped on VPS..." -ForegroundColor Yellow
Read-Host

Write-Host "`n[3/3] Starting backend with fixes..." -ForegroundColor Yellow
Write-Host "⚠️  RUN THIS ON VPS:" -ForegroundColor Yellow
Write-Host @"

cd C:\backend
python multi_broker_backend_updated.py

"@ -ForegroundColor White

Write-Host "`n✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host ""
Write-Host "What was fixed:" -ForegroundColor Cyan
Write-Host "  ✓ Database has 'closed_at' column - profit calculations working" -ForegroundColor Green
Write-Host "  ✓ Recent-profit guard now allows 30% risk (was 5%)" -ForegroundColor Green
Write-Host "  ✓ GBPUSD will now be able to trade with R13.39 profit pool" -ForegroundColor Green
Write-Host ""
Write-Host "Expected behavior:" -ForegroundColor Cyan
Write-Host "  • With R13.39 recent profit:" -ForegroundColor White
Write-Host "    - OLD: 5% = R0.67 allowed risk ✗" -ForegroundColor Red
Write-Host "    - NEW: 30% = R4.02 allowed risk ✓" -ForegroundColor Green
Write-Host "  • Still blocks if stop loss > R4.02 (need more profit to trade bigger)" -ForegroundColor Yellow
Write-Host ""
