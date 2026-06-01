import sqlite3
conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()
cursor.execute("SELECT trade_id, symbol, status, ticket FROM trades WHERE status = 'open'")
open_trades = cursor.fetchall()
print('Open trades in database:')
for trade in open_trades:
    print(f'  {trade[0]}: {trade[1]} status={trade[2]} ticket={trade[3]}')
cursor.execute("SELECT trade_id, symbol, status, ticket FROM trades WHERE symbol LIKE '%RIF%'")
rif_trades = cursor.fetchall()
print('RIF trades in database:')
for trade in rif_trades:
    print(f'  {trade[0]}: {trade[1]} status={trade[2]} ticket={trade[3]}')
conn.close()