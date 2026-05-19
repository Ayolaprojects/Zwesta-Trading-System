"""
Deep profit investigation - find the $65/$59 and understand daily reset behaviour.
"""
import sqlite3, json
from collections import defaultdict

db = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

# ── 1. All-time profit summary per bot from trades table ─────────────────────
print("="*70)
print("ALL-TIME PROFIT PER BOT (from trades table)")
print("="*70)
rows = conn.execute("""
    SELECT bot_id,
           COUNT(*) as trades,
           SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
           SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
           SUM(profit) as total_profit,
           MAX(profit) as best_trade,
           MIN(profit) as worst_trade,
           MIN(time_open) as first_trade,
           MAX(COALESCE(time_close, time_open)) as last_trade
    FROM trades
    GROUP BY bot_id
    ORDER BY total_profit DESC
""").fetchall()
for r in rows:
    print(f"\n  {r['bot_id']}")
    print(f"  Trades: {r['trades']} | Wins: {r['wins']} | Losses: {r['losses']}")
    print(f"  Total P&L: ${r['total_profit']:.4f}")
    print(f"  Best: ${r['best_trade']:.4f} | Worst: ${r['worst_trade']:.4f}")
    print(f"  Period: {r['first_trade']} → {r['last_trade']}")

# ── 2. Profit by DATE for main bot ────────────────────────────────────────────
print()
print("="*70)
print("DAILY P&L for bot_1778970971191 (Binance spot)")
print("="*70)
daily = conn.execute("""
    SELECT substr(COALESCE(time_close, time_open), 1, 10) as day,
           COUNT(*) as trades,
           SUM(profit) as daily_pnl,
           SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) as gross_wins,
           SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END) as gross_losses
    FROM trades
    WHERE bot_id = 'bot_1778970971191'
    GROUP BY day
    ORDER BY day DESC
    LIMIT 14
""").fetchall()
for d in daily:
    sign = '+' if (d['daily_pnl'] or 0) >= 0 else ''
    print(f"  {d['day']} | trades={d['trades']} | P&L={sign}${d['daily_pnl']:.2f} | wins=${d['gross_wins']:.2f} | losses=${d['gross_losses']:.2f}")

# ── 3. Check runtime_state history snapshots ──────────────────────────────────
print()
print("="*70)
print("RUNTIME_STATE snapshots - looking for $65/$59 peak")
print("="*70)
try:
    for bot_id in ['bot_1778970971191', 'bot_1778970611374', 'bot_1779011553325']:
        rs_row = conn.execute("SELECT runtime_state FROM user_bots WHERE bot_id=?", (bot_id,)).fetchone()
        if rs_row and rs_row[0]:
            rs = json.loads(rs_row[0])
            print(f"\n  {bot_id}")
            # Look for any profit-related keys
            for k, v in sorted(rs.items()):
                if any(x in k.lower() for x in ['profit', 'peak', 'daily', 'total', 'pnl', 'win', 'loss', 'trade']):
                    print(f"    {k}: {v}")
except Exception as e:
    print(f"  Error: {e}")

# ── 4. Check bot_monitoring table ─────────────────────────────────────────────
print()
print("="*70)
print("BOT_MONITORING snapshots (profit history)")
print("="*70)
try:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(bot_monitoring)").fetchall()]
    print("  Columns:", cols)
    rows = conn.execute("""
        SELECT * FROM bot_monitoring ORDER BY created_at DESC LIMIT 10
    """).fetchall()
    for r in rows:
        print("  ", dict(r))
except Exception as e:
    print(f"  bot_monitoring: {e}")

# ── 5. Check binance_orders actual columns ────────────────────────────────────
print()
print("="*70)
print("BINANCE_ORDERS table structure + recent records")
print("="*70)
try:
    cols = [r[1] for r in conn.execute("PRAGMA table_info(binance_orders)").fetchall()]
    print("  Columns:", cols)
    rows = conn.execute("SELECT * FROM binance_orders ORDER BY rowid DESC LIMIT 10").fetchall()
    for r in rows:
        print("  ", dict(r))
except Exception as e:
    print(f"  binance_orders: {e}")

conn.close()
