import sqlite3
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Check for RIFUSDT trades
cursor.execute("SELECT trade_id, symbol, status, profit, ticket, time_open, broker FROM trades WHERE symbol LIKE '%RIF%'")
rif_trades = cursor.fetchall()
print('RIFUSDT trades in VPS database:')
for trade in rif_trades:
    trade_id, symbol, status, profit, ticket, time_open, broker = trade
    print(f'  {trade_id}: {symbol} status={status} profit={profit} ticket={ticket} broker={broker}')

# Check all open trades
cursor.execute("SELECT trade_id, symbol, status, profit, ticket, time_open, broker FROM trades WHERE status = 'open'")
open_trades = cursor.fetchall()
print(f'\nOpen trades in VPS database ({len(open_trades)} total):')
for trade in open_trades:
    trade_id, symbol, status, profit, ticket, time_open, broker = trade
    print(f'  {trade_id}: {symbol} status={status} profit={profit} ticket={ticket} broker={broker}')

# Check recent trades
cursor.execute("SELECT trade_id, symbol, status, profit, ticket, time_open, broker FROM trades ORDER BY created_at DESC LIMIT 10")
recent_trades = cursor.fetchall()
print(f'\nRecent trades in VPS database:')
for trade in recent_trades:
    trade_id, symbol, status, profit, ticket, time_open, broker = trade
    print(f'  {trade_id}: {symbol} status={status} profit={profit} ticket={ticket} broker={broker}')

conn.close()