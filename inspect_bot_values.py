import os
import sqlite3

paths = [
    r'C:\backend\zwesta_trading.db',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zwesta_trading.db'),
]
bot_ids = ['1780678113048', '178090663839']
for path in paths:
    print('DB:', path)
    if not os.path.exists(path):
        print('  NOT FOUND')
        continue
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row['name'] for row in cur.fetchall()]
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [(row['name'], row['type']) for row in cur.fetchall()]
        for colname, coltype in cols:
            if coltype and coltype.lower() not in {'text', 'varchar', 'char', 'integer', 'int', 'bigint'}:
                continue
            for bot_id in bot_ids:
                try:
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE {colname} = ?", (bot_id,))
                    cnt = cur.fetchone()['cnt']
                    if cnt:
                        print(f"  {table}.{colname} exact {bot_id}: {cnt}")
                except Exception:
                    pass
                try:
                    cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE {colname} LIKE ?", (f'%{bot_id}%',))
                    cnt = cur.fetchone()['cnt']
                    if cnt:
                        print(f"  {table}.{colname} like {bot_id}: {cnt}")
                except Exception:
                    pass
    conn.close()
