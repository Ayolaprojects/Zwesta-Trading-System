# VPS DEPLOY INSTRUCTIONS (run as Administrator on VPS via RDP)
# Bundle date: 2026-05-17 (volatility override fix + maxDailyLoss/riskPerTrade auto-scaling)

# WHAT THIS DEPLOY ADDS (over previous VPS state):
#   * [CRITICAL] Binance volatility override threshold: 64.0 -> 40.0
#       - Fixes "Medium volatility not in allowed set" block on Binance crypto bots
#       - Allows Medium-volatility entries when signal strength >= 40 (was 64)
#       - Affects: strong_crypto_volatility_override in _should_enter_trade_gate
#   * maxDailyLoss / riskPerTrade auto-scaling by account balance (assisted mode)
#       - If balance >= 50 USDT: maxDailyLoss = balance * 0.02, riskPerTrade = balance * 0.005
#       - Only raises values; never lowers below user-configured amount
#   * [PREVIOUS] Post-close cooldown for MT5/Exness (60 min default)
#   * [PREVIOUS] Adaptive symbol-performance gate
#   * [PREVIOUS] Position-age timeout for Binance spot (>4h auto-SELL)
#   * New Exness optimizer (_optimize_exness.py): threshold=65 manual + 60m cooldown
#   * Updated Binance VPS optimizer (_optimize_vps.py): sets maxPositionAgeHours/agedClosePnlFloor


1. Stop the backend
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'multi_broker_backend' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

2. Backup current backend + DB
   Copy-Item C:\backend\multi_broker_backend_updated.py C:\backend\multi_broker_backend_updated.py.bak.2026-05-06b -Force
   Copy-Item C:\backend\zwesta_trading.db C:\backend\zwesta_trading.db.bak.2026-05-06b -Force

3. Copy patched backend (assumes bundle uploaded to C:\Temp\_vps_deploy_bundle):
   Copy-Item C:\Temp\_vps_deploy_bundle\multi_broker_backend_updated.py C:\backend\multi_broker_backend_updated.py -Force
   # If your bundle includes the system/ folder this round, refresh it too; otherwise skip.
   if (Test-Path C:\Temp\_vps_deploy_bundle\system) { Copy-Item C:\Temp\_vps_deploy_bundle\system\* C:\backend\system\ -Recurse -Force }
   Remove-Item C:\backend\__pycache__ -Recurse -Force -ErrorAction SilentlyContinue

4. Copy + run BINANCE optimizer (threshold=2 manual, $50 trade, age-timeout 4h):
   Copy-Item C:\Temp\_vps_deploy_bundle\_optimize_vps.py C:\backend\_optimize_vps.py -Force
   cd C:\backend
   & "C:\Program Files\Python311\python.exe" _optimize_vps.py

5. Copy + run EXNESS optimizer (threshold=65 manual, 60m post-close cooldown):
   Copy-Item C:\Temp\_vps_deploy_bundle\_optimize_exness.py C:\backend\_optimize_exness.py -Force
   cd C:\backend
   & "C:\Program Files\Python311\python.exe" _optimize_exness.py

6. Restart backend:
   cd C:\backend
   Start-Process -FilePath "C:\Program Files\Python311\python.exe" -ArgumentList "multi_broker_backend_updated.py" -RedirectStandardOutput C:\backend\backend.log -RedirectStandardError C:\backend\backend.err -WindowStyle Hidden

7. Verify (after ~60s):
   Get-Content C:\backend\backend.err -Tail 60
   # Expected new log lines:
   #   "[BALANCE] Bot xxx: equity trend = growing/flat/shrinking ..."
   #   "[RISK] Bot xxx ..."         (existing risk gate)
   #   "POSITION_AGE_TIMEOUT"       (Binance spot, only when a stale position auto-SELLs)
   #   "Post-close cooldown set on <SYM> for 60m"  (Exness only, after a close)
   # Should NOT see:
   #   "HIT CUMULATIVE"             (gated by winningTrades>=5)
   #   "drawdown XX%" before bot has any wins
