import sqlite3, json
db = r"C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db"
c = sqlite3.connect(db); c.row_factory = sqlite3.Row
cur = c.cursor()

print("=== user_bots ===")
for r in cur.execute("SELECT bot_id, name, strategy, status, enabled, symbols, updated_at FROM user_bots"):
    print(dict(r))

print("\n=== Recent trades (newest 20) ===")
for r in cur.execute("SELECT trade_id, bot_id, symbol, order_type, profit, status, time_open, time_close, created_at FROM trades ORDER BY created_at DESC LIMIT 20"):
    print(dict(r))

print("\n=== runtime_state per bot ===")
for r in cur.execute("SELECT bot_id, runtime_state FROM user_bots"):
    rs = r['runtime_state']
    if not rs: 
        print(r['bot_id'], "<empty>")
        continue
    try:
        d = json.loads(rs)
    except Exception as e:
        print(r['bot_id'], "parse err", e); continue
    keys = ['status','pauseReason','lastNoTradeReason','lastNoTradeAt','lossStreakPauseUntil',
            'drawdownPauseUntil','symbolReentryCooldowns','symbol_cooldowns','open_positions',
            'totalProfit','totalTrades','adaptiveSignalThresholdOffset','effectiveMaxOpenPositions']
    print(f"\n--- bot {r['bot_id']} ---")
    for k in keys:
        if k in d:
            v = d[k]
            if isinstance(v, dict) and len(v) > 8:
                print(f"  {k}: <{len(v)} entries>")
            else:
                print(f"  {k}: {v}")
