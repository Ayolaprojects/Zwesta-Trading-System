import sqlite3
conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()
cursor.execute("SELECT trade_id, symbol, status, profit, ticket, time_open, time_close FROM trades ORDER BY created_at DESC LIMIT 10")
recent_trades = cursor.fetchall()
print('Recent trades:')
for trade in recent_trades:
    trade_id, symbol, status, profit, ticket, time_open, time_close = trade
    print(f'  {trade_id}: {symbol} status={status} profit={profit} ticket={ticket}')
    print(f'    Open: {time_open}, Close: {time_close}')
conn.close()