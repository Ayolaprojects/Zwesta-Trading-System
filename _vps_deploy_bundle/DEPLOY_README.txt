# VPS DEPLOY INSTRUCTIONS (run as Administrator on VPS via RDP)
# Bundle date: 2026-06-04 (bot summary live Binance snapshot refresh + duplicate-backend cleanup)

# WHAT THIS DEPLOY ADDS (over previous VPS state):
#   * [CRITICAL] `/api/bot/summary` now refreshes Binance/FXCM bot cards from cached live broker snapshots
#       - Fixes app bot cards staying unchanged for hours while Binance workers continue trading
#       - Applies to dashboard/bot-list cards; analytics already used live Binance snapshots
#   * [CRITICAL] `start_zwesta_backend.ps1` now kills duplicate `multi_broker_backend_updated.py` processes
#       - Prevents stale runtime state from surviving behind a healthy port 9000 listener
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

4. Apply tuned BINANCE bot state for bot_1779229018996 (DB-side runtime_state fix):
   Copy-Item C:\Temp\_vps_deploy_bundle\_apply_binance_bot_1779229018996_aggressive_state.py C:\backend\_apply_binance_bot_1779229018996_aggressive_state.py -Force
   cd C:\backend
   & "C:\Program Files\Python311\python.exe" _apply_binance_bot_1779229018996_aggressive_state.py --db C:\backend\zwesta_trading.db

5. Copy + run BINANCE optimizer (general threshold=2 manual, but preserves the tuned override for bot_1779229018996):
   Copy-Item C:\Temp\_vps_deploy_bundle\_optimize_vps.py C:\backend\_optimize_vps.py -Force
   cd C:\backend
   & "C:\Program Files\Python311\python.exe" _optimize_vps.py

6. Copy + run EXNESS optimizer (threshold=65 manual, 60m post-close cooldown):
   Copy-Item C:\Temp\_vps_deploy_bundle\_optimize_exness.py C:\backend\_optimize_exness.py -Force
   cd C:\backend
   & "C:\Program Files\Python311\python.exe" _optimize_exness.py

7. Copy the single-instance launcher:
   Copy-Item C:\Temp\_vps_deploy_bundle\start_zwesta_backend.ps1 C:\backend\start_zwesta_backend.ps1 -Force

8. Restart backend through the launcher (preferred; cleans duplicate backend processes first):
   powershell -NoProfile -ExecutionPolicy Bypass -File C:\backend\start_zwesta_backend.ps1

9. Verify (after ~60s):
   Get-Content C:\backend\backend.err -Tail 60
   wmic process where "name='python.exe' and commandline like '%multi_broker_backend_updated.py%'" get ProcessId,CreationDate,CommandLine /format:list
   netstat -ano | findstr :9000
   # Expected new log lines:
   #   "[BALANCE] Bot xxx: equity trend = growing/flat/shrinking ..."
   #   "[RISK] Bot xxx ..."         (existing risk gate)
   #   "POSITION_AGE_TIMEOUT"       (Binance spot, only when a stale position auto-SELLs)
   #   "Post-close cooldown set on <SYM> for 60m"  (Exness only, after a close)
   # Bot cards should now show brokerSnapshotDataSource of live/cached-live instead of runtime-cache for Binance bots.
   # Should NOT see:
   #   "HIT CUMULATIVE"             (gated by winningTrades>=5)
   #   "drawdown XX%" before bot has any wins
