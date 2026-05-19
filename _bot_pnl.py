import sqlite3, json
conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

bot = 'bot_1777949277150'
cur.execute("SELECT trade_id, symbol, volume, price, profit, status, created_at, updated_at FROM trades WHERE bot_id = ? AND created_at >= '2026-05-05' ORDER BY created_at", (bot,))
rows = [dict(r) for r in cur.fetchall()]
print(f"Total trades for {bot} on May 5: {len(rows)}\n")
total_pnl = 0.0
by_sym = {}
for r in rows:
    p = r['profit'] or 0.0
    total_pnl += p
    by_sym.setdefault(r['symbol'], []).append(p)
    print(f"{r['created_at'][:19]} {r['symbol']:10} qty={r['volume']:<8} px={r['price']:<10} pnl={p:+.3f} status={r['status']}")
print(f"\nTotal P&L: {total_pnl:+.3f} USDT")
print("\nPer-symbol summary:")
for sym, pnls in by_sym.items():
    wins = sum(1 for p in pnls if p > 0)
    losses = sum(1 for p in pnls if p < 0)
    flat = sum(1 for p in pnls if p == 0)
    print(f"  {sym:10} trades={len(pnls):3}  wins={wins:3}  losses={losses:3}  flat={flat:3}  net={sum(pnls):+.3f}")
