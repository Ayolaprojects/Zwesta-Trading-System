import sqlite3
from runtime_infrastructure import get_database_path

path = get_database_path()
print('DBPATH:', path)
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

bot_ids = ['1780678113048', '178090663839']
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cur.fetchall()]

for table in tables:
    try:
        cur.execute(f"PRAGMA table_info({table})")
        cols = [row['name'] for row in cur.fetchall()]
    except sqlite3.OperationalError:
        continue
    if 'bot_id' not in cols:
        continue
    for bot_id in bot_ids:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE bot_id = ?", (bot_id,))
        cnt = cur.fetchone()['cnt']
        if cnt:
            print(f"{table}: {bot_id} -> {cnt}")

conn.close()
