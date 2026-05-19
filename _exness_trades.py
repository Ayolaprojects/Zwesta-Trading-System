import sqlite3, json
db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Exness bot trades - all time, recent 30
print('=== EXNESS BOT TRADES (recent 30) ===')
cur.execute("""
    SELECT bot_id, ticket, symbol, order_type, volume, price, profit, 
           status, time_open, time_close, trade_data
    FROM trades
    WHERE bot_id IN ('bot_1779185407301','bot_1779197221415','bot_1779201336253')
    ORDER BY time_open DESC
    LIMIT 30
""")
for r in cur.fetchall():
    td = json.loads(r['trade_data'] or '{}') if r['trade_data'] else {}
    direction = td.get('direction','') or td.get('type','') or r['order_type']
    reason = td.get('closeReason','')
    lots = td.get('lots','') or td.get('lotSize','') or r['volume']
    print(f"  [{r['status']}] {r['symbol']} {direction} lots={lots} profit={r['profit']} "
          f"open={str(r['time_open'])[:16]} close={str(r['time_close'])[:16] if r['time_close'] else 'open'} "
          f"reason={reason} bot=...{r['bot_id'][-10:]}")

# Yesterday's profitable bot trades
print()
print('=== PROFITABLE BOT FROM YESTERDAY (bot_1779029733318_cf54807) ===')
cur.execute("""
    SELECT bot_id, ticket, symbol, order_type, volume, profit, status, time_open, trade_data
    FROM trades
    WHERE bot_id = 'bot_1779029733318_cf54807'
    ORDER BY time_open DESC
    LIMIT 15
""")
for r in cur.fetchall():
    td = json.loads(r['trade_data'] or '{}') if r['trade_data'] else {}
    print(f"  [{r['status']}] {r['symbol']} profit={r['profit']} open={str(r['time_open'])[:16]}")

# Compare lot sizes / tradeAmounts between old and current active bots
print()
print('=== RUNTIME STATE - tradeAmount in DB ===')
cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE status='active'")
for r in cur.fetchall():
    rs = json.loads(r['runtime_state'] or '{}') if r['runtime_state'] else {}
    print(f"  {r['bot_id']}: tradeAmount={rs.get('tradeAmount')} effectiveTradeAmount={rs.get('effectiveTradeAmount')} "
          f"PSM={rs.get('effectivePositionSizeMultiplier')} profile={rs.get('managementProfile')}")

db.close()
