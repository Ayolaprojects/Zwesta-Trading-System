import sqlite3, json
c = sqlite3.connect(r'C:\backend\zwesta_trading.db'); c.row_factory = sqlite3.Row
for r in c.execute("SELECT bot_id, status, enabled FROM user_bots"):
    print(r['bot_id'], 'status=', r['status'], 'enabled=', r['enabled'])
print('---open positions counts---')
for r in c.execute("SELECT bot_id, runtime_state FROM user_bots"):
    s = json.loads(r['runtime_state'] or '{}')
    op = s.get('open_positions') or {}
    print(r['bot_id'], 'open=', len(op), list(op.keys()))
