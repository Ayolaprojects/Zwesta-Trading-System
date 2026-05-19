import sqlite3
conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)
for t in tables:
    if 'bot' in t.lower() or 'config' in t.lower():
        cur.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in cur.fetchall()]
        print(f"{t}: {cols}")
conn.close()
