import sqlite3, json

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
bot_id = 'bot_1779229018996'

rows = db.execute(
    'SELECT trade_id, symbol, profit, time_open, time_close, trade_data '
    'FROM trades WHERE bot_id=? AND profit=-6.21 LIMIT 5', (bot_id,)
).fetchall()

for r in rows:
    td = json.loads(r['trade_data']) if r['trade_data'] else {}
    print(f"trade={r['trade_id']} symbol={r['symbol']} profit={r['profit']}")
    print(f"  open={r['time_open']}  close={r['time_close']}")
    print(f"  closeReason={td.get('closeReason','?')}  side={td.get('side','?')}")
    print(f"  entryPrice={td.get('entryPrice','?')}  exitPrice={td.get('exitPrice','?')}")
    print(f"  qty={td.get('qty','?')}  notional={td.get('notional','?')}")
    print(f"  maxHoldMins={td.get('maxHoldMinutes','?')}  holdMins={td.get('holdMinutes','?')}")
    print()

# Also check all unique close reasons for losses
print("=== All close reasons for loss trades ===")
rows2 = db.execute(
    'SELECT trade_data FROM trades WHERE bot_id=? AND profit<-1.0', (bot_id,)
).fetchall()
reasons = {}
for r in rows2:
    td = json.loads(r['trade_data']) if r['trade_data'] else {}
    reason = td.get('closeReason', 'NO_REASON')
    reasons[reason] = reasons.get(reason, 0) + 1
for k, v in sorted(reasons.items()):
    print(f"  {v}x  {k}")

db.close()
