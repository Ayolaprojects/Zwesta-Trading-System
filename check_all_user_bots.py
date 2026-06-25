import sqlite3
import json

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check ALL user_bots
cur.execute("SELECT bot_id, status, runtime_state FROM user_bots WHERE user_id='8e74db37-fd1e-4c57-87c4-ad3b64012ecf'")
rows = cur.fetchall()
for row in rows:
    print(f'bot_id: {row[0]}')
    print(f'  status: {row[1]}')
    if row[2]:
        try:
            data = json.loads(row[2])
            pos = data.get('open_positions', {})
            print(f'  open_positions: {len(pos)} positions')
            for k, v in pos.items():
                if isinstance(v, dict):
                    print(f'    {k}: {v.get("symbol")} @{v.get("entryPrice")}')
        except Exception as e:
            print(f'  Error parsing runtime_state: {e}')
    else:
        print('  No runtime_state')

conn.close()