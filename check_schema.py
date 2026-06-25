import sqlite3

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check bot_credentials schema
cur.execute("PRAGMA table_info(bot_credentials)")
print('bot_credentials schema:')
for row in cur.fetchall():
    print(f'  {row}')

# Check all credentials
cur.execute("SELECT * FROM bot_credentials")
print('\nbot_credentials data:')
for row in cur.fetchall():
    print(f'  {row}')

conn.close()