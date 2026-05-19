import sqlite3, json
con = sqlite3.connect(r"C:\backend\zwesta_trading.db")
con.row_factory = sqlite3.Row
cur = con.cursor()
print("=== ALL OPEN trades for user 8e74db37 ===")
cur.execute("SELECT trade_id, bot_id, ticket, symbol, status, volume, price, profit, time_open, time_close, created_at FROM trades WHERE user_id=? AND status IN ('open','OPEN','active','ACTIVE','pending') ORDER BY created_at DESC", ("8e74db37-fd1e-4c57-87c4-ad3b64012ecf",))
for r in cur.fetchall():
    print(dict(r))

print("\n=== Counts by bot_id and status ===")
cur.execute("SELECT bot_id, status, COUNT(*) FROM trades GROUP BY bot_id, status")
for r in cur.fetchall():
    print(tuple(r))
