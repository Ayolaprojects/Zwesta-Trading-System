import sqlite3, os, sys
db = r"C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db"
c = sqlite3.connect(db)
cur = c.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("TABLES:", tables)
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM '{t}'")
        n = cur.fetchone()[0]
        cur.execute(f"PRAGMA table_info('{t}')")
        cols = [r[1] for r in cur.fetchall()]
        print(f"\n== {t} ({n} rows) cols={cols}")
    except Exception as e:
        print(t, "ERR", e)
