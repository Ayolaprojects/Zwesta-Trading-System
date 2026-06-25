import sqlite3
import json

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Search for this bot
cur.execute("SELECT bot_id, user_id, status, runtime_state FROM user_bots WHERE bot_id LIKE '%1782305458924%'")
rows = cur.fetchall()
for row in rows:
    print(f'bot_id: {row[0]}')
    print(f'  user_id: {row[1]}')
    print(f'  status: {row[2]}')
    if row[3]:
        try:
            data = json.loads(row[3])
            pos = data.get('open_positions', {})
            print(f'  open_positions: {len(pos)} positions')
            for k, v in pos.items():
                if isinstance(v, dict):
                    print(f'    {k}: {v.get("symbol")} @{v.get("entryPrice")}')
        except Exception as e:
            print(f'  Error parsing runtime_state: {e}')

conn.close()