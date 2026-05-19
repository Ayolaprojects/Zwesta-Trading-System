import json, sqlite3
from datetime import datetime
c = sqlite3.connect(r'C:\backend\zwesta_trading.db'); c.row_factory = sqlite3.Row
rows = c.execute("SELECT bot_id, runtime_state FROM user_bots WHERE user_id='8e74db37-fd1e-4c57-87c4-ad3b64012ecf'").fetchall()
now = datetime.now()
for r in rows:
    rs = json.loads(r['runtime_state'] or '{}')
    op = rs.get('open_positions') or {}
    print(f"\n{r['bot_id']}: open={len(op)}")
    for tk, p in op.items():
        et = p.get('entryTime') or p.get('time') or ''
        age = ''
        try:
            age = f" age={(now - datetime.fromisoformat(str(et).replace('Z',''))).total_seconds()/3600:.1f}h"
        except Exception:
            pass
        print(f"  {tk} {p.get('symbol')} {p.get('type')} entry@{p.get('entryPrice')} cur@{p.get('currentPrice')} pnl={p.get('profit')}{age}")
c.close()
