"""
Try to read user_bots using row-by-row approach to bypass corruption.
"""
import sqlite3, json

src = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(src)
conn.row_factory = sqlite3.Row

# Try to read individual rows using ROWID scan
try:
    max_rowid = conn.execute('SELECT MAX(rowid) FROM user_bots').fetchone()[0]
    print(f'Max rowid: {max_rowid}')
except Exception as e:
    print(f'Cannot get max rowid: {e}')
    max_rowid = 200

recovered = []
for rid in range(1, (max_rowid or 200) + 1):
    try:
        row = conn.execute('SELECT rowid, * FROM user_bots WHERE rowid=?', (rid,)).fetchone()
        if row:
            recovered.append(dict(row))
    except Exception:
        pass

print(f'Recovered {len(recovered)} rows from user_bots')
for r in recovered:
    bot_id = r.get('bot_id', 'unknown')
    status = r.get('status', '?')
    rs = r.get('runtime_state', '{}') or '{}'
    try:
        state = json.loads(rs)
        eta = state.get('effectiveTradeAmount', 'N/A')
        rpt = state.get('riskPerTrade', 'N/A')
    except Exception:
        eta = rpt = 'parse error'
    print(f'  [{r["rowid"]}] {bot_id} status={status} effectiveTradeAmount={eta} riskPerTrade={rpt}')

conn.close()
