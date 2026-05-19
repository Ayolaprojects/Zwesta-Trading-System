import sqlite3, json

db = r'C:\backend\zwesta_trading.db'
bot_id = 'bot_1778970971191'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables:', tables)

# Check user_bots
if 'user_bots' in tables:
    cols = [d[1] for d in c.execute('PRAGMA table_info(user_bots)').fetchall()]
    print('user_bots cols:', cols[:15])
    row = c.execute('SELECT * FROM user_bots WHERE bot_id=?', (bot_id,)).fetchone()
    if row:
        d = dict(row)
        # show keys
        print('user_bots keys:', list(d.keys()))
        # show config snippet
        for k in ['config', 'runtime_state', 'bot_config']:
            if k in d:
                val = d[k]
                if val:
                    parsed = json.loads(val) if isinstance(val, str) else val
                    pp = parsed.get('profitProtection', {})
                    print(f'{k}.profitProtection:', json.dumps(pp, indent=2)[:500])
    else:
        print('Bot not found in user_bots')

conn.close()
