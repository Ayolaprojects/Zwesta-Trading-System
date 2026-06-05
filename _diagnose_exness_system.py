"""EXNESS SYSTEM HEALTH CHECK - Diagnose core trading issues"""
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("="*80)
print("EXNESS SYSTEM DIAGNOSTIC - ROOT CAUSE ANALYSIS")
print("="*80)

# 1. Check for data quality issues
print("\n1️⃣  DATA QUALITY CHECK")
print("-" * 80)

cur.execute("SELECT COUNT(*) as cnt FROM trades WHERE bot_id LIKE 'bot_%' AND profit IS NULL")
null_profits = cur.fetchone()['cnt']
print(f"   Trades with NULL profit: {null_profits}")

cur.execute("SELECT COUNT(*) as cnt FROM trades WHERE time_close IS NULL AND status = 'closed'")
missing_close = cur.fetchone()['cnt']
print(f"   Closed trades missing close time: {missing_close}")

# 2. Check for position stacking (multiple open trades same symbol)
print("\n2️⃣  POSITION STACKING CHECK")
print("-" * 80)

cur.execute("""
    SELECT symbol, COUNT(*) as open_count, GROUP_CONCAT(bot_id) as bots
    FROM trades
    WHERE status = 'open'
    GROUP BY symbol
    HAVING open_count > 1
""")

stacked = cur.fetchall()
if stacked:
    print("   ❌ STACKED POSITIONS DETECTED:")
    for row in stacked:
        print(f"      {row['symbol']}: {row['open_count']} open trades from {len(set(row['bots'].split(','))) if row['bots'] else 0} bots")
else:
    print("   ✓ No problematic stacking detected")

# 3. Check lot size consistency
print("\n3️⃣  LOT SIZE DRIFT CHECK")
print("-" * 80)

symbols_with_lots = defaultdict(list)
cur.execute("""
    SELECT symbol, volume, profit, time_open
    FROM trades
    WHERE status = 'closed'
    ORDER BY time_open DESC
    LIMIT 200
""")

for row in cur.fetchall():
    symbols_with_lots[row['symbol']].append((row['volume'], row['profit']))

print("   Lot size patterns (last 200 closed trades):")
for symbol in sorted(symbols_with_lots.keys()):
    lots = [l[0] for l in symbols_with_lots[symbol]]
    avg_lot = sum(lots) / len(lots)
    max_lot = max(lots)
    min_lot = min(lots)
    
    # Check if losses correlate with larger lots
    profits = [l[1] for l in symbols_with_lots[symbol]]
    losses = [p for p in profits if p < 0]
    loss_lots = [lots[i] for i in range(len(lots)) if profits[i] < 0]
    avg_loss_lot = sum(loss_lots) / len(loss_lots) if loss_lots else 0
    avg_win_lot = sum([lots[i] for i in range(len(lots)) if profits[i] > 0]) / len([p for p in profits if p > 0]) if [p for p in profits if p > 0] else 0
    
    print(f"      {symbol}: avg={avg_lot:.2f}, range={min_lot:.2f}-{max_lot:.2f}")
    if avg_loss_lot > 0 and avg_win_lot > 0:
        print(f"         Loss trades avg: {avg_loss_lot:.2f}, Win trades avg: {avg_win_lot:.2f}")
        if avg_loss_lot > avg_win_lot * 1.5:
            print(f"         ⚠️  PROBLEM: Losses have {(avg_loss_lot/avg_win_lot):.1f}x larger position size!")

# 4. Check signal quality (win rate trend)
print("\n4️⃣  SIGNAL QUALITY TREND")
print("-" * 80)

symbols_to_check = ['AUDUSDm', 'GBPUSDm', 'USDJPYm', 'XAUUSDm']
for symbol in symbols_to_check:
    cur.execute("""
        SELECT profit FROM trades 
        WHERE symbol = ?
        ORDER BY time_open DESC
        LIMIT 50
    """, (symbol,))
    
    recent = cur.fetchall()
    if len(recent) >= 10:
        recent_10 = recent[:10]
        older_40 = recent[10:50]
        
        recent_wr = len([r for r in recent_10 if r['profit'] > 0]) / len(recent_10) * 100
        older_wr = len([r for r in older_40 if r['profit'] > 0]) / len(older_40) * 100
        
        trend = "📉 DEGRADING" if recent_wr < older_wr - 10 else "📈 IMPROVING" if recent_wr > older_wr + 10 else "➡️ STABLE"
        print(f"      {symbol}: Recent 10: {recent_wr:.0f}% vs Older 40: {older_wr:.0f}% {trend}")

# 5. Check for systematic issues (all losses in same timeframe)
print("\n5️⃣  TIMING/SESSION ANALYSIS")
print("-" * 80)

cur.execute("""
    SELECT DATE(time_close) as trade_date, 
           COUNT(*) as total_trades,
           SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
           SUM(profit) as daily_pnl
    FROM trades
    WHERE status = 'closed'
    GROUP BY DATE(time_close)
    ORDER BY trade_date DESC
    LIMIT 10
""")

print("   Last 10 trading days:")
for row in cur.fetchall():
    date = row['trade_date']
    total = row['total_trades']
    wins = row['wins']
    wr = (wins / total * 100) if total > 0 else 0
    pnl = row['daily_pnl']
    status = "✓" if pnl > 0 else "✗"
    print(f"      {date}: {total} trades, {wr:.0f}% win rate, {pnl:+.2f} {status}")

# 6. Current runtime config issues
print("\n6️⃣  BOT CONFIGURATION CHECK")
print("-" * 80)

cur.execute("""
    SELECT bot_id, runtime_state FROM user_bots 
    WHERE broker_account_id LIKE 'Exness_%'
""")

for bot_row in cur.fetchall():
    rs = json.loads(bot_row['runtime_state'] or '{}')
    
    issues = []
    if rs.get('signalThreshold', 0) < 50:
        issues.append("⚠️ Low signal threshold")
    if rs.get('effectivePositionSizeMultiplier', 1) > 1.5:
        issues.append("⚠️ High position size multiplier")
    if not rs.get('managementProfile'):
        issues.append("⚠️ No management profile")
    if rs.get('adaptiveSignalThresholdOffset', 0) != 0:
        issues.append("⚠️ Adaptive offset enabled")
    
    print(f"\n   {bot_row['bot_id'][-12:]}:")
    if issues:
        for issue in issues:
            print(f"      {issue}")
    else:
        print(f"      ✓ Configuration looks OK")
    
    print(f"      Threshold: {rs.get('signalThreshold')}")
    print(f"      PSM: {rs.get('effectivePositionSizeMultiplier', 1)}")
    print(f"      Profile: {rs.get('managementProfile')}")

db.close()

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
