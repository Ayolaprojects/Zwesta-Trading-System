import os
import sqlite3

paths = [
    r'C:\backend\zwesta_trading.db',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zwesta_trading.db'),
]
for path in paths:
    print('CHECK', path, 'EXISTS', os.path.exists(path))
    if not os.path.exists(path):
        continue
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row['name'] for row in cur.fetchall()]
    print('  TABLES:', len(tables))
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [row['name'] for row in cur.fetchall()]
        if 'bot_id' not in cols:
            continue
        for bot_id in ['1780678113048', '178090663839']:
            cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE bot_id = ?", (bot_id,))
            cnt = cur.fetchone()['cnt']
            if cnt:
                print(f"  {table}: {bot_id} -> {cnt}")
    conn.close()
