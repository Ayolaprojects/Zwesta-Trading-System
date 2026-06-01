import sqlite3
conn = sqlite3.connect('zwesta_trading.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM trades')
print('Trades count:', c.fetchone()[0])
c.execute('SELECT trade_id, bot_id, symbol, order_type, volume, status, created_at FROM trades ORDER BY created_at DESC LIMIT 5')
print('Recent trades:')
for row in c.fetchall():
    print(row)
conn.close()