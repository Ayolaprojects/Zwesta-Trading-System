import sqlite3
db = sqlite3.connect(r'C:\backend\zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Find tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

for t in ['trades', 'bot_trades', 'trade_log', 'trade_history', 'closed_trades']:
    if t in tables:
        cur.execute(f'PRAGMA table_info({t})')
        cols = [r['name'] for r in cur.fetchall()]
        print(f'{t} columns: {cols}')
        cur.execute(f'SELECT COUNT(*) as cnt FROM {t}')
        cnt = cur.fetchone()['cnt']
        print(f'{t} total rows: {cnt}')
db.close()
