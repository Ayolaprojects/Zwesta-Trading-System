import sqlite3
conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT trade_id, symbol, status, profit, ticket, time_open, time_close FROM trades WHERE symbol LIKE "%RIF%"')
rif_trades = cursor.fetchall()
print('All RIF trades in database:')
for trade in rif_trades:
    trade_id, symbol, status, profit, ticket, time_open, time_close = trade
    print(f'  {trade_id}: {symbol} status={status} profit={profit} ticket={ticket}')
    print(f'    Open: {time_open}, Close: {time_close}')
cursor.execute('SELECT COUNT(*) FROM trades')
total_trades = cursor.fetchone()[0]
print(f'Total trades in database: {total_trades}')
conn.close()