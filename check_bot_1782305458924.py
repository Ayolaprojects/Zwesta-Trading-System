import sqlite3
import json

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Check the new bot
cur.execute("SELECT bot_id, symbols, status, runtime_state FROM user_bots WHERE bot_id='bot_1782305458924'")
row = cur.fetchone()
if row:
    bot_id, symbols, status, rs = row
    print(f'Bot: {bot_id}')
    print(f'Status: {status}')
    print(f'Symbols: {symbols}')
    if rs:
        data = json.loads(rs)
        print(f'Open positions: {len(data.get("open_positions", {}))}')
        for ticket, pos in data.get('open_positions', {}).items():
            print(f'  {ticket}: {pos.get("symbol")} @ {pos.get("entryPrice")} ({pos.get("type")})')
        print(f'ProfitProtection: {data.get("profitProtection")}')

# Check bot_credentials link
cur.execute("SELECT bot_id, credential_id FROM bot_credentials WHERE bot_id='bot_1782305458924'")
cred = cur.fetchone()
if cred:
    print(f'\nLinked to credential: {cred[1]}')
else:
    print('\nWARNING: No credential link - bot cannot trade!')

conn.close()