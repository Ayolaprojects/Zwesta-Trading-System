import sqlite3
DB = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
# Check user_bots schema
if 'user_bots' in tables:
    cur.execute("PRAGMA table_info(user_bots)")
    cols = [r[1] for r in cur.fetchall()]
    print('user_bots columns:', cols[:20])
    cur.execute("SELECT bot_id FROM user_bots LIMIT 5")
    bots = [r[0] for r in cur.fetchall()]
    print('Sample bot_ids:', bots)
conn.close()
