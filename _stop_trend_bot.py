import sqlite3

# Stop the poorly performing trend-following bot
bot_id = 'bot_1779796196293_live_1779797860435'
db_path = 'C:/backend/zwesta_trading.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Disable the bot
cursor.execute("UPDATE user_bots SET enabled=0, status='STOPPED' WHERE bot_id=?", (bot_id,))
conn.commit()
print(f'✅ Disabled bot {bot_id} - {cursor.rowcount} row(s) updated')

# Verify
cursor.execute("SELECT bot_id, enabled, status, broker_type FROM user_bots WHERE bot_id=?", (bot_id,))
result = cursor.fetchone()
if result:
    print(f'Verified: bot_id={result[0]}, enabled={result[1]}, status={result[2]}, broker={result[3]}')
else:
    print(f'⚠️ Bot {bot_id} not found in database')

conn.close()
