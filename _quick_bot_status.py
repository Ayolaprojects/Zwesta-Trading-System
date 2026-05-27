import sqlite3

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row

rows = db.execute('SELECT bot_id, broker, status, enabled, profit FROM user_bots').fetchall()
print(f'Total bots: {len(rows)}')
for r in rows:
    bid = r['bot_id'] if 'broker' not in db.execute('PRAGMA table_info(user_bots)').fetchall()[0].keys() else r['bot_id']
    # get all columns
    print(f"  {r['bot_id']} | status={r['status']} | enabled={r['enabled']} | profit={r['profit']}")

db.close()
