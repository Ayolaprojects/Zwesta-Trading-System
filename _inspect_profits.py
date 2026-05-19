"""
Inspect profit history from zwesta_trading.db
"""
import sqlite3, json
from datetime import datetime

db = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

print("="*70)
print("BOT DAILY PROFITS (from user_bots runtime_state)")
print("="*70)
# Read runtime_state for each bot
rows = conn.execute("SELECT bot_id, name, status, is_live FROM user_bots").fetchall()
for r in rows:
    bot_id = r['bot_id']
    # Try to get runtime_state via overflow read trick
    try:
        rs_row = conn.execute(
            "SELECT runtime_state FROM user_bots WHERE bot_id=?", (bot_id,)
        ).fetchone()
        if rs_row and rs_row[0]:
            rs = json.loads(rs_row[0])
            dp = rs.get('dailyProfit', 'N/A')
            tp = rs.get('totalProfit', 'N/A')
            trades = rs.get('totalTrades', 'N/A')
            wins = rs.get('winTrades', 'N/A')
            peak = rs.get('peakDailyProfit', rs.get('peakProfit', 'N/A'))
            print(f"\n  Bot: {bot_id}")
            print(f"  Status: {r['status']} | is_live={r['is_live']}")
            print(f"  dailyProfit:  ${dp}")
            print(f"  totalProfit:  ${tp}")
            print(f"  peakProfit:   ${peak}")
            print(f"  trades: {trades} (wins: {wins})")
            # Open positions
            positions = rs.get('openPositions') or rs.get('positions') or []
            if isinstance(positions, list) and positions:
                print(f"  Open positions ({len(positions)}):")
                for p in positions[:5]:
                    sym = p.get('symbol','?')
                    profit = p.get('profit', p.get('unrealizedPnl', '?'))
                    print(f"    {sym}: ${profit}")
            elif isinstance(positions, dict):
                for sym, p in list(positions.items())[:5]:
                    profit = p.get('profit', p.get('unrealizedPnl', '?'))
                    print(f"    {sym}: ${profit}")
    except Exception as e:
        print(f"  Bot {bot_id}: runtime_state error: {e}")

print()
print("="*70)
print("TRADES TABLE (last 30 closed trades with profit)")
print("="*70)
try:
    trades = conn.execute("""
        SELECT t.bot_id, t.symbol, t.order_type, t.profit, t.volume,
               t.time_open, t.time_close, t.status
        FROM trades t
        WHERE t.profit IS NOT NULL AND t.profit != 0
        ORDER BY t.time_close DESC, t.created_at DESC
        LIMIT 30
    """).fetchall()
    if trades:
        total = 0
        for t in trades:
            profit = t['profit'] or 0
            total += float(profit)
            print(f"  {t['bot_id'][:20]} | {t['symbol']} | {t['order_type']} | profit=${profit:.4f} | {t['time_close'] or t['time_open']}")
        print(f"\n  TOTAL closed profit in DB: ${total:.4f}")
    else:
        print("  No closed trades with profit found.")
except Exception as e:
    print(f"  Error reading trades: {e}")

print()
print("="*70)
print("BINANCE_ORDERS TABLE (last 20)")
print("="*70)
try:
    orders = conn.execute("""
        SELECT bot_id, symbol, side, status, executed_qty, price, realized_pnl, created_at
        FROM binance_orders
        ORDER BY created_at DESC
        LIMIT 20
    """).fetchall()
    if orders:
        for o in orders:
            pnl = o['realized_pnl']
            print(f"  {o['symbol']} {o['side']} | qty={o['executed_qty']} | price={o['price']} | pnl={pnl} | {o['status']} | {o['created_at']}")
    else:
        print("  No Binance orders recorded.")
except Exception as e:
    print(f"  Error (table may not exist): {e}")

print()
print("="*70)
print("PAUSE_EVENTS / PROFIT SNAPSHOTS")
print("="*70)
try:
    events = conn.execute("""
        SELECT bot_id, event_type, profit_at_pause, created_at
        FROM pause_events
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    for e in events:
        print(f"  {e['bot_id']} | {e['event_type']} | profit={e['profit_at_pause']} | {e['created_at']}")
except Exception as e:
    print(f"  pause_events: {e}")

conn.close()
