import sqlite3
import os
# Search all known db locations
paths = [
    r'C:\backend\zwesta_trading.db',
    r'C:\zwesta-trader\zwesta_trading.db',
    r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db',
    r'C:\zwesta-trader\xm_trading_system\zwesta_trading.db',
]
target = 'bot_1777361409656'
for p in paths:
    if not os.path.exists(p):
        print(f"-- not found: {p}")
        continue
    try:
        c = sqlite3.connect(p).cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_bots'")
        if not c.fetchone():
            print(f"-- no user_bots: {p}")
            continue
        c.execute("SELECT bot_id, name, enabled, status FROM user_bots WHERE bot_id LIKE ?", (f"%{target[-15:]}%",))
        rows = c.fetchall()
        print(f"{p}: {len(rows)} matches")
        for r in rows:
            print(" ", r)
        c.execute("SELECT COUNT(*) FROM user_bots")
        print(f"  total bots: {c.fetchone()[0]}")
    except Exception as e:
        print(f"  ERROR: {e}")
