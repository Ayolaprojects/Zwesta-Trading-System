import sqlite3

db = sqlite3.connect('C:/backend/zwesta_trading.db')

# Re-enable the two disabled Exness bots
db.execute(
    "UPDATE user_bots SET enabled=1, status='STOPPED' "
    "WHERE bot_id IN ('bot_1779436757590','bot_1779470513636')"
)
db.commit()

# Verify
rows = db.execute('SELECT bot_id, status, enabled, total_profit FROM user_bots').fetchall()
print(f'Total bots: {len(rows)}')
for r in rows:
    print(f'  {r[0]} | status={r[1]} | enabled={r[2]} | profit={r[3]}')

db.close()
print('Done.')
