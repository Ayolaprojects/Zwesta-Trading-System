# Quick VPS Backend Restart Script
# Run this to apply all the quality gate and profit guard fixes

Write-Host "`n🔄 RESTARTING VPS BACKEND..." -ForegroundColor Cyan

# Find and kill the backend process
Write-Host "`n1. Finding backend process..." -ForegroundColor Yellow
$netstat = netstat -ano | Select-String ":9000"
if ($netstat) {
    $pid = ($netstat -split '\s+')[-1]
    Write-Host "   Found process on port 9000: PID $pid" -ForegroundColor Green
    taskkill /F /PID $pid
    Start-Sleep -Seconds 2
} else {
    Write-Host "   No process found on port 9000" -ForegroundColor Gray
}

# Copy updated backend file to VPS
Write-Host "`n2. Copying updated backend to VPS..." -ForegroundColor Yellow
try {
    Copy-Item "c:\zwesta-trader\Zwesta Flutter App\multi_broker_backend_updated.py" `
              -Destination "C:\backend\multi_broker_backend_updated.py" -Force
    Write-Host "   ✓ Backend file updated" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Error copying file: $_" -ForegroundColor Red
}

# Start backend
Write-Host "`n3. Starting backend with new code..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\backend; python multi_broker_backend_updated.py"

Write-Host "`n✅ BACKEND RESTARTING!" -ForegroundColor Green
Write-Host "`nNew settings active:" -ForegroundColor Cyan
Write-Host "  • Setup quality gate: 5.5/10 (was 7.0)" -ForegroundColor White
Write-Host "  • Recent-profit guard: 30% (was 5%)" -ForegroundColor White
Write-Host "  • Max profit guard: 50% (was 25%)" -ForegroundColor White
Write-Host "`nMonitor logs for:" -ForegroundColor Cyan
Write-Host "  • '30.0% of last 4 closed trades' (confirms new profit guard)" -ForegroundColor White
Write-Host "  • Setup scores 5.5+ being ACCEPTED (not rejected)" -ForegroundColor White
Write-Host "`nPress Ctrl+C in the new window to stop backend`n" -ForegroundColor Gray
