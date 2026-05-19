"""Tune trade-frequency cadence on VPS bots.

Problem: bots have no `tradingMode`/`tradingInterval`/`pollInterval` saved in
runtime_state, so the runtime defaults to interval mode @ 300s (5 minutes).
This makes Binance feel stagnant, especially given the SPOT BUY-only pattern.

Fix: write signal-driven mode + 60s cycle + 5s signal poll.
- Binance bots get aggressive cadence (crypto = 24/7, REST is fast).
- Exness/MT5 bots get a slightly slower cadence (90s) to respect the shared
  MT5 terminal lock when multiple MT5 accounts coexist.

Does NOT touch: tradeAmount, signalThreshold, intelligentScanner, autoSwitch,
risk gates, HWM, or trade history. Only cadence fields.

Usage:
    python _tune_cadence_vps.py
"""
import json, sqlite3
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()

# Cadence presets
BINANCE_CADENCE = {
    'tradingMode': 'signal-driven',
    'tradingInterval': 60,   # 1 minute between full cycles
    'pollInterval': 5,       # check signal every 5s when in poll loop
}
MT5_CADENCE = {
    'tradingMode': 'signal-driven',
    'tradingInterval': 90,   # respect shared MT5 terminal lock
    'pollInterval': 8,
}

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
cur = c.cursor()

rows = cur.execute(
    "SELECT bot_id, name, broker_account_id, runtime_state FROM user_bots"
).fetchall()

patched = 0
for r in rows:
    bid = r['bot_id']
    broker_acc = r['broker_account_id'] or ''
    s = json.loads(r['runtime_state'] or '{}')
    if broker_acc.startswith('Binance_'):
        cadence = BINANCE_CADENCE
        label = 'Binance'
    else:
        cadence = MT5_CADENCE
        label = 'MT5/Exness'
    before = {k: s.get(k) for k in cadence}
    s.update(cadence)
    cur.execute(
        "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
        (json.dumps(s), NOW, bid),
    )
    patched += 1
    print(f"[CADENCE] {bid} ({label}): before={before} -> after={cadence}")

c.commit()
c.close()
print(f"\nDone. Patched {patched} bot(s).")
print("Restart backend for cadence changes to take effect:")
print("  Get-Process python | Where-Object {$_.MainWindowTitle -like '*backend*'} | Stop-Process")
print("  cd C:\\backend; Start-Process python -ArgumentList 'multi_broker_backend_updated.py' -RedirectStandardOutput backend.log -RedirectStandardError backend.err")
