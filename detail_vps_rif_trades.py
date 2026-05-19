import sqlite3
from datetime import datetime
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Get detailed info about the RIFUSDT trades
cursor.execute("SELECT * FROM trades WHERE symbol = 'RIFUSDT' AND status = 'open'")
rif_trades = cursor.fetchall()

print('Detailed RIFUSDT open trades:')
for trade in rif_trades:
    trade_dict = {
        'trade_id': trade[0],
        'bot_id': trade[1],
        'user_id': trade[2],
        'symbol': trade[3],
        'order_type': trade[4],
        'volume': trade[5],
        'price': trade[6],
        'profit': trade[7],
        'commission': trade[8],
        'swap': trade[9],
        'ticket': trade[10],
        'time_open': trade[11],
        'time_close': trade[12],
        'status': trade[13],
        'created_at': trade[14],
        'updated_at': trade[15],
        'trade_data': trade[16],
        'timestamp': trade[17],
        'broker': trade[18]
    }
    print(f"\nTrade ID: {trade_dict['trade_id']}")
    print(f"  Bot ID: {trade_dict['bot_id']}")
    print(f"  User ID: {trade_dict['user_id']}")
    print(f"  Symbol: {trade_dict['symbol']}")
    print(f"  Order Type: {trade_dict['order_type']}")
    print(f"  Volume: {trade_dict['volume']}")
    print(f"  Price: {trade_dict['price']}")
    print(f"  Profit: {trade_dict['profit']}")
    print(f"  Ticket: {trade_dict['ticket']}")
    print(f"  Broker: {trade_dict['broker']}")
    print(f"  Status: {trade_dict['status']}")
    print(f"  Time Open: {trade_dict['time_open']}")
    print(f"  Created At: {trade_dict['created_at']}")
    if trade_dict['timestamp']:
        dt = datetime.fromtimestamp(trade_dict['timestamp'] / 1000)
        print(f"  Timestamp: {dt}")

# Check which bot these belong to
cursor.execute("SELECT bot_id, symbols, broker_type FROM user_bots WHERE bot_id IN ('bot_1777234994531', 'bot_1777235140561_7dc40c1b', 'bot_1777238322914')")
bots = cursor.fetchall()
print(f"\nBot configurations:")
for bot in bots:
    bot_id, symbols, broker_type = bot
    print(f"  {bot_id}: symbols={symbols}, broker_type={broker_type}")

conn.close()