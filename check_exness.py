import sqlite3
import json

conn = sqlite3.connect(r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db')
cur = conn.cursor()

# Check Exness credentials
cur.execute("SELECT credential_id, user_id, account_number, password, server, is_live FROM broker_credentials WHERE broker_name LIKE '%Exness%'")
creds = cur.fetchall()
print(f'Exness credentials found: {len(creds)}')
for c in creds:
    print(f'  Account: {c[2]}, Server: {c[4]}, Live: {c[5]}')

# Check all bots and their broker types from runtime_state
cur.execute("SELECT bot_id, status, symbols, runtime_state FROM user_bots")
bots = cur.fetchall()
print(f'\nAll bots found: {len(bots)}')
for b in bots:
    runtime = b[3]
    broker = 'unknown'
    if runtime:
        try:
            rs = json.loads(runtime) if isinstance(runtime, str) else runtime
            broker = rs.get('brokerType', rs.get('broker_type', rs.get('broker', 'unknown'))) or 'unknown'
        except:
            broker = 'unknown'
    broker = str(broker).lower()
    
    if 'exness' in broker or 'mt5' in broker or 'metatrader' in broker or 'forex' in broker:
        print(f'  EXNESS/MT5 Bot: {b[0]}, Broker: {broker}, Status: {b[1]}')
    else:
        print(f'  Binance Bot: {b[0]}, Symbols: {b[2]}')

conn.close()