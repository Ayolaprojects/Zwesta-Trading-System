import sqlite3
import json

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check the bot's runtime state for open position
cur.execute("SELECT bot_id, runtime_state, symbols FROM user_bots WHERE bot_id='bot_1782305458924'")
row = cur.fetchone()
if row:
    print(f'bot_1782305458924:')
    print(f'  symbols: {row[2]}')
    if row[1]:
        data = json.loads(row[1])
        pos = data.get('open_positions', {})
        print(f'  open_positions count: {len(pos)}')
        for k, v in pos.items():
            print(f'    {k}: {v}')

conn.close()