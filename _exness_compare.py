"""Compare lot sizes and profits between today's Exness bots and the old profitable bots."""
import sqlite3, json

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Find the bot_1779029733318_cf54807 - was it deleted? Check user_bots including non-active
print('=== ALL USER_BOTS (including deleted) ===')
cur.execute("SELECT bot_id, status, enabled, daily_profit, total_profit, created_at, updated_at FROM user_bots ORDER BY created_at DESC")
for r in cur.fetchall():
    print(f"  {r['bot_id']} status={r['status']} enabled={r['enabled']} daily={r['daily_profit']} total={r['total_profit']}")

# Get biggest profitable Exness trades from all time
print()
print('=== MOST PROFITABLE EXNESS TRADES EVER ===')
cur.execute("""
    SELECT bot_id, symbol, order_type, volume, profit, time_open, trade_data
    FROM trades
    WHERE bot_id LIKE 'bot_%' AND profit > 50
    ORDER BY profit DESC
    LIMIT 20
""")
for r in cur.fetchall():
    td = json.loads(r['trade_data'] or '{}') if r['trade_data'] else {}
    lots = td.get('lots','') or td.get('lotSize','') or r['volume']
    print(f"  +{r['profit']} | {r['symbol']} lots={lots} open={str(r['time_open'])[:16]} bot=...{r['bot_id'][-15:]}")

# What were the lot sizes in the profitable bot?
print()
print('=== bot_1779029733318_cf54807 ALL TRADES ===')
cur.execute("""
    SELECT symbol, order_type, volume, profit, time_open, trade_data
    FROM trades
    WHERE bot_id = 'bot_1779029733318_cf54807'
    ORDER BY time_open DESC
    LIMIT 20
""")
for r in cur.fetchall():
    td = json.loads(r['trade_data'] or '{}') if r['trade_data'] else {}
    lots = td.get('lots','') or td.get('lotSize','') or r['volume']
    direction = td.get('direction','') or r['order_type']
    print(f"  {r['symbol']} {direction} lots={lots} profit={r['profit']} open={str(r['time_open'])[:16]}")

db.close()
