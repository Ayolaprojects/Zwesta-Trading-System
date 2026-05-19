import sqlite3, json

db = sqlite3.connect("C:/backend/zwesta_trading.db")
c = db.cursor()

# Check runtime_state structure
c.execute("SELECT bot_id, runtime_state FROM user_bots WHERE enabled=1 LIMIT 2")
for bot_id, rs in c.fetchall():
    print(f"--- {bot_id} ---")
    try:
        s = json.loads(rs) if rs else {}
        print(f"  keys: {list(s.keys())}")
        thresh = s.get("signal_threshold", s.get("signalThreshold", "N/A"))
        settings = s.get("settings", {})
        if settings:
            thresh = settings.get("signalThreshold", settings.get("signal_threshold", thresh))
        print(f"  threshold: {thresh}")
    except Exception as e:
        print(f"  parse error: {e}")
        print(f"  raw: {str(rs)[:300]}")

print()
print("=== OPEN TRADES ===")
c.execute("SELECT trade_id, bot_id, symbol, status FROM trades WHERE status='open' OR status='OPEN' OR status='active' OR status='ACTIVE'")
rows = c.fetchall()
print(f"Count: {len(rows)}")
for r in rows:
    print(r)

db.close()
