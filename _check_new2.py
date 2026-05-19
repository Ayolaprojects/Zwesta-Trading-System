import sqlite3, json
c = sqlite3.connect('C:/backend/zwesta_trading.db')
print('--- New bot trades ---')
rows = c.execute("SELECT bot_id, symbol, order_type, volume, price, profit, ticket, status, time_open FROM trades WHERE bot_id='bot_1777949277150' ORDER BY created_at DESC").fetchall()
for r in rows: print(r)
print('TOTAL DB rows for new bot:', len(rows))

print('\n--- Open trades across all bots ---')
rows2 = c.execute("SELECT bot_id, symbol, order_type, volume, price, ticket, time_open FROM trades WHERE status='open' ORDER BY created_at DESC").fetchall()
for r in rows2: print(r)

print('\n--- Runtime state for bot_1777949277150 ---')
rs = c.execute("SELECT runtime_state FROM user_bots WHERE bot_id='bot_1777949277150'").fetchone()
if rs and rs[0]:
    d = json.loads(rs[0])
    op = d.get('open_positions', {})
    print('Open positions:', len(op))
    for k, v in op.items():
        print(f"  {k}: {v.get('symbol')} {v.get('type')} vol={v.get('volume')} entry={v.get('entryPrice')} current={v.get('currentPrice')} profit={v.get('profit')} time={v.get('entryTime')}")
    th = d.get('tradeHistory', [])
    print('Trade history:', len(th))
else:
    print('No runtime state')
