"""Quick inspection of bots + trade history for the active user."""
import json
import sqlite3

DB = r'C:\backend\zwesta_trading.db'
USER = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
rows = c.execute(
    "SELECT bot_id, broker_account_id, runtime_state FROM user_bots WHERE user_id = ?",
    (USER,),
).fetchall()

print(f'Total bots: {len(rows)}')
print()
for r in rows:
    rs = json.loads(r['runtime_state'] or '{}')
    th = rs.get('tradeHistory') or []
    closed = [t for t in th if str(t.get('status') or '').lower() == 'closed']
    by_sym = {}
    for t in closed:
        sym = t.get('symbol', '?')
        by_sym.setdefault(sym, []).append(float(t.get('profit') or 0))
    sym_breakdown = ', '.join(
        f"{s}={len(p)}/${round(sum(p), 2)}" for s, p in sorted(by_sym.items())
    ) or '(no closed)'
    print(
        f"{r['bot_id'][-20:]:20s} | {r['broker_account_id']:25s} | "
        f"symbols={rs.get('symbols')} | totalProfit={rs.get('totalProfit')} | "
        f"closed={len(closed)} | {sym_breakdown}"
    )
c.close()
