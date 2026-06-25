import sqlite3
import json

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check user credentials
cur.execute("SELECT credential_id, broker, account FROM user_credentials")
print('User credentials:')
for row in cur.fetchall():
    print(f'  credential_id={row[0]}, broker={row[1]}, account={row[2]}')

# Check the bot's runtime state for position details
cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE bot_id='bot_1782305458924'")
row = cur.fetchone()
if row and row[1]:
    data = json.loads(row[1])
    print(f'\nbot_1782305458924 runtime_state:')
    print(f'  open_positions: {json.dumps(data.get("open_positions", {}), indent=4)}')

conn.close()