import sqlite3

# Connect to database
conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()

# Get all table names
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

print('📋 DATABASE TABLES:')
for table in tables:
    print(f'   {table[0]}')

# Check user_bots table
try:
    cursor.execute('SELECT COUNT(*) FROM user_bots')
    bot_count = cursor.fetchone()[0]
    print(f'\n🤖 Total bots in database: {bot_count}')

    cursor.execute('SELECT COUNT(*) FROM user_bots WHERE enabled = 1')
    active_count = cursor.fetchone()[0]
    print(f'🤖 Active bots: {active_count}')

    # Check recent bots
    cursor.execute('SELECT bot_id, name, status, created_at FROM user_bots ORDER BY created_at DESC LIMIT 3')
    recent_bots = cursor.fetchall()

    print('\n📅 RECENT BOTS:')
    for bot in recent_bots:
        bot_id, name, status, created_at = bot
        print(f'   {bot_id[:30]}...: {name} (status: {status})')

except Exception as e:
    print(f'❌ Error checking bots: {e}')

conn.close()