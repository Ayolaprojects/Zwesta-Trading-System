import sqlite3

conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print('📋 DATABASE TABLES:')
for table in tables:
    print(f'   {table[0]}')

# Check bot count
cursor.execute('SELECT COUNT(*) FROM user_bots WHERE enabled = 1 AND status = ?', ('active',))
active_count = cursor.fetchone()[0]
print(f'\n📊 BOT STATUS:')
print(f'   Active enabled bots: {active_count}')

conn.close()