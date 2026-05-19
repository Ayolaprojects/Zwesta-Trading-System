import sqlite3
import json
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Get trade_data for RIFUSDT trades
cursor.execute("SELECT trade_id, trade_data FROM trades WHERE symbol = 'RIFUSDT' AND status = 'open'")
rif_trades = cursor.fetchall()

print('Trade data for RIFUSDT trades:')
for trade_id, trade_data_json in rif_trades:
    print(f'\nTrade {trade_id}:')
    if trade_data_json:
        try:
            trade_data = json.loads(trade_data_json)
            print(f'  {json.dumps(trade_data, indent=2)}')
        except json.JSONDecodeError:
            print(f'  Invalid JSON: {trade_data_json}')
    else:
        print('  No trade_data')

# Check if there are any logs or errors in the database
cursor.execute("SELECT * FROM bot_monitoring WHERE bot_id IN ('bot_1777235140561_7dc40c1b', 'bot_1777238322914') ORDER BY created_at DESC LIMIT 10")
monitoring = cursor.fetchall()
print(f'\nRecent bot monitoring entries:')
for entry in monitoring:
    print(f'  {entry}')

conn.close()