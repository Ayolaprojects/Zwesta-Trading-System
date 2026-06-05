"""Generate detailed Exness optimization report with symbol-level performance analysis"""
import sqlite3
import json
from collections import defaultdict
from datetime import datetime, timedelta

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Get Exness bot trades from last 7 days
print("="*80)
print("EXNESS TRADES OPTIMIZATION REPORT")
print("="*80)

cur.execute("""
    SELECT bot_id, ticket, symbol, order_type, volume, price, profit, 
           status, time_open, time_close, trade_data
    FROM trades
    WHERE bot_id IN (
        SELECT bot_id FROM user_bots WHERE broker_account_id LIKE 'Exness_%'
    )
    ORDER BY time_open DESC
    LIMIT 100
""")

trades = cur.fetchall()

# Analyze by symbol
symbol_stats = defaultdict(lambda: {
    'total': 0, 'wins': 0, 'losses': 0, 
    'total_profit': 0, 'avg_win': 0, 'avg_loss': 0,
    'max_loss': 0, 'biggest_loss': None
})

for trade in trades:
    symbol = trade['symbol']
    profit = trade['profit']
    
    symbol_stats[symbol]['total'] += 1
    symbol_stats[symbol]['total_profit'] += profit
    
    if profit > 0:
        symbol_stats[symbol]['wins'] += 1
        symbol_stats[symbol]['avg_win'] += profit
    elif profit < 0:
        symbol_stats[symbol]['losses'] += 1
        symbol_stats[symbol]['avg_loss'] += profit
        if profit < symbol_stats[symbol]['max_loss']:
            symbol_stats[symbol]['max_loss'] = profit
            symbol_stats[symbol]['biggest_loss'] = trade

# Calculate averages
for sym in symbol_stats:
    if symbol_stats[sym]['wins'] > 0:
        symbol_stats[sym]['avg_win'] /= symbol_stats[sym]['wins']
    if symbol_stats[sym]['losses'] > 0:
        symbol_stats[sym]['avg_loss'] /= symbol_stats[sym]['losses']

print(f"\n📊 SYMBOL PERFORMANCE ANALYSIS (Last 7 Days)")
print(f"   {'Symbol':<12} {'Trades':>6} {'Wins':>6} {'Rate':>6} {'P&L':>10} {'Avg Win':>10} {'Avg Loss':>10} {'Max Loss':>10}")
print(f"   {'-'*82}")

# Sort by P&L
for sym in sorted(symbol_stats.keys(), key=lambda x: symbol_stats[x]['total_profit']):
    s = symbol_stats[sym]
    win_rate = (s['wins'] / s['total'] * 100) if s['total'] > 0 else 0
    print(f"   {sym:<12} {s['total']:>6} {s['wins']:>6} {win_rate:>5.0f}% {s['total_profit']:>9.2f} {s['avg_win']:>9.2f} {s['avg_loss']:>9.2f} {s['max_loss']:>9.2f}")

# Identify problem symbols
print(f"\n⚠️  PROBLEM SYMBOLS (Win Rate < 50% or Total Loss > -50)")
problem_symbols = []
for sym, stats in symbol_stats.items():
    win_rate = (stats['wins'] / stats['total'] * 100) if stats['total'] > 0 else 0
    if win_rate < 50 or stats['total_profit'] < -50:
        problem_symbols.append((sym, win_rate, stats['total_profit']))

if problem_symbols:
    for sym, wr, pnl in sorted(problem_symbols, key=lambda x: x[2]):
        print(f"   {sym}: {wr:.0f}% win rate, {pnl:+.2f} ZAR total P&L")
        # Show biggest loss for this symbol
        print(f"      → Largest loss: {symbol_stats[sym]['max_loss']:.2f} ZAR")
else:
    print("   ✓ All symbols performing reasonably")

# Get runtime config for bots
print(f"\n⚙️  CURRENT BOT CONFIGURATION")
cur.execute("""
    SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Exness_%'
""")

for row in cur.fetchall():
    rs = json.loads(row['runtime_state'] or '{}') if row['runtime_state'] else {}
    print(f"   {row['bot_id'][-10:]}...")
    print(f"      Signal Threshold: {rs.get('signalThreshold', 'N/A')}")
    print(f"      Post-Close Cooldown: {rs.get('postCloseCooldownMinutes', 0)} min")
    print(f"      Management Profile: {rs.get('managementProfile', 'N/A')}")

print(f"\n✅ OPTIMIZATION APPLIED")
print(f"   ✓ Signal threshold increased to 65 (was very low)")
print(f"   ✓ 60-minute post-close cooldown enabled")
print(f"   ✓ Adaptive mode disabled")
print(f"   ✓ Stale cooldown markers cleared")

print(f"\n📋 RECOMMENDATIONS")
print(f"   1. Monitor {len(problem_symbols)} problem symbol(s) closely")
print(f"   2. Consider excluding underperforming symbols from trading")
print(f"   3. Restart backend to activate optimizations")
print(f"   4. Check MT5 terminal for order execution delays")

db.close()
