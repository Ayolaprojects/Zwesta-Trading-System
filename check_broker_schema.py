import sqlite3

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check broker_credentials schema
cur.execute("PRAGMA table_info(broker_credentials)")
print('broker_credentials schema:')
for row in cur.fetchall():
    print(f'  {row}')

# Check broker_credentials data
cur.execute("SELECT * FROM broker_credentials")
print('\nbroker_credentials data:')
for row in cur.fetchall():
    print(f'  {row}')

conn.close()