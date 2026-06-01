import sqlite3
import json
conn = sqlite3.connect('zwesta_trading.db')
c = conn.cursor()
c.execute("SELECT ub.bot_id, ub.name, ub.strategy, ub.status, ub.enabled FROM user_bots ub WHERE ub.status='active'")
print('All active bots:')
for row in c.fetchall():
    print(f'  {row[0]}: {row[1]} - {row[2]} - status: {row[3]} - enabled: {row[4]}')
conn.close()