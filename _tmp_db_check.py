import sqlite3
conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM {t}")
    cnt = cur.fetchone()[0]
    if cnt > 0:
        print(f"  {t}: {cnt} rows")
conn.close()
