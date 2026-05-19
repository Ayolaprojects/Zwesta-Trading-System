import sqlite3
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Get user_bots table schema
cursor.execute("PRAGMA table_info(user_bots)")
schema = cursor.fetchall()
print('user_bots table schema:')
for col in schema:
    print(f'  {col[1]}: {col[2]}')

# Check bot configurations
cursor.execute("SELECT bot_id, symbols FROM user_bots WHERE bot_id IN ('bot_1777234994531', 'bot_1777235140561_7dc40c1b', 'bot_1777238322914')")
bots = cursor.fetchall()
print(f"\nBot configurations:")
for bot in bots:
    bot_id, symbols = bot
    print(f"  {bot_id}: symbols={symbols}")

conn.close()