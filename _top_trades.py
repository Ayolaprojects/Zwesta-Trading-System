import sqlite3, json
db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

cur.execute('SELECT DISTINCT bot_id FROM trades WHERE profit > 100 ORDER BY bot_id')
print('Bots with profit>100 per trade:')
for r in cur.fetchall():
    print(' ', r['bot_id'])

cur.execute("""
    SELECT bot_id, symbol, volume, profit, time_open, trade_data
    FROM trades
    WHERE profit > 80
    ORDER BY time_open DESC
    LIMIT 15
""")
print('\nTop 15 most profitable trades:')
for r in cur.fetchall():
    td = json.loads(r['trade_data'] or '{}') if r['trade_data'] else {}
    lots = td.get('lots','') or td.get('lotSize','') or r['volume']
    print(f"  {r['symbol']} lots={lots} profit={r['profit']} open={str(r['time_open'])[:16]} bot={r['bot_id']}")
db.close()
