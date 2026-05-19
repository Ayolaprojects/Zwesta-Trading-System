import sqlite3

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM trades WHERE bot_id = ?', ('bot_1777238322914',))
result = cursor.fetchall()
print('Trades for bot bot_1777238322914:')
for row in result:
    print(row)
conn.close()