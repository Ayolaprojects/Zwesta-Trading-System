import sqlite3

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check all credentials
cur.execute("SELECT credential_id, broker, account FROM bot_credentials")
for row in cur.fetchall():
    print(f'credential_id={row[0]}, broker={row[1]}, account={row[2]}')

# Check all bots
cur.execute("SELECT bot_id, symbols, status, runtime_state FROM user_bots")
for row in cur.fetchall():
    print(f'\nbot_id={row[0]}')
    print(f'  status={row[2]}')
    if row[3]:
        import json
        data = json.loads(row[3])
        positions = data.get('open_positions', {})
        print(f'  open_positions={len(positions)}')

conn.close()