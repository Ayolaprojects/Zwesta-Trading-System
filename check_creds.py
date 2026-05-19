import sqlite3

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM broker_credentials WHERE credential_id = ?', ('e568ec38-cfc7-4b05-8033-b56ecdf304e4',))
result = cursor.fetchall()
print('Credentials:')
for row in result:
    print(row)
conn.close()