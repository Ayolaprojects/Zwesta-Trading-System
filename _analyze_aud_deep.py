"""Deep analysis of AUDUSDm - investigating profitability history"""
import sqlite3
import json

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("="*80)
print("AUDUSSM DETAILED ANALYSIS - COMPLETE HISTORY")
print("="*80)

# Get ALL AUDUSDm trades
cur.execute("""
    SELECT bot_id, ticket, symbol, order_type, volume, price, profit, 
           status, time_open, time_close, trade_data
    FROM trades
    WHERE symbol = 'AUDUSDm'
    ORDER BY time_open DESC
""")

trades = cur.fetchall()

if not trades:
    print("\n❌ NO AUDUSDm TRADES FOUND IN DATABASE")
    db.close()
    exit(1)

print(f"\n📊 TOTAL AUDUSDm TRADES: {len(trades)}")

# Calculate stats
total_profit = sum(t['profit'] for t in trades)
wins = len([t for t in trades if t['profit'] > 0])
losses = len([t for t in trades if t['profit'] < 0])
breakeven = len([t for t in trades if t['profit'] == 0])

win_rate = (wins / len(trades) * 100) if trades else 0
avg_win = sum(t['profit'] for t in trades if t['profit'] > 0) / wins if wins > 0 else 0
avg_loss = sum(t['profit'] for t in trades if t['profit'] < 0) / losses if losses > 0 else 0

print(f"\n💰 PROFITABILITY STATS:")
print(f"   Total P&L: {total_profit:+.2f} ZAR")
print(f"   Wins: {wins} ({win_rate:.1f}%)")
print(f"   Losses: {losses} ({(losses/len(trades)*100):.1f}%)")
print(f"   Breakeven: {breakeven}")
print(f"   Avg Win: {avg_win:+.2f} ZAR")
print(f"   Avg Loss: {avg_loss:+.2f} ZAR")

print(f"\n📋 RECENT TRADES (Last 20):")
print(f"   {'Date':<20} {'Type':<6} {'Lots':<6} {'Price':<10} {'P&L':<8} {'Status':<8}")
print(f"   {'-'*80}")

for trade in trades[:20]:
    date_str = str(trade['time_open'])[:16] if trade['time_open'] else 'N/A'
    trade_type = trade['order_type'][:3].upper()
    lots = trade['volume']
    price = trade['price']
    pnl = trade['profit']
    status = "✓" if pnl > 0 else "✗" if pnl < 0 else "="
    
    print(f"   {date_str:<20} {trade_type:<6} {lots:<6.2f} {price:<10.5f} {pnl:>7.2f} {status:<8}")

print(f"\n🎯 TREND ANALYSIS:")
print(f"   By decade (chronological):")
recent_10 = trades[:10]
mid_10 = trades[10:20] if len(trades) > 10 else []
older = trades[20:] if len(trades) > 20 else []

if recent_10:
    r_wins = len([t for t in recent_10 if t['profit'] > 0])
    r_pnl = sum(t['profit'] for t in recent_10)
    print(f"      Last 10:  {r_wins}/10 wins, {r_pnl:+.2f} ZAR")

if mid_10:
    m_wins = len([t for t in mid_10 if t['profit'] > 0])
    m_pnl = sum(t['profit'] for t in mid_10)
    print(f"      Mid 10:   {m_wins}/10 wins, {m_pnl:+.2f} ZAR")

if older:
    o_wins = len([t for t in older if t['profit'] > 0])
    o_pnl = sum(t['profit'] for t in older)
    print(f"      Older ({len(older)}):  {o_wins}/{len(older)} wins, {o_pnl:+.2f} ZAR")

# Check current portfolio
print(f"\n⚠️  CURRENT STATUS:")
cur.execute("""
    SELECT bot_id, runtime_state FROM user_bots 
    WHERE broker_account_id LIKE 'Exness_%'
    LIMIT 1
""")
bot = cur.fetchone()
if bot:
    rs = json.loads(bot['runtime_state'] or '{}')
    is_disabled = rs.get('symbol_config', {}).get('AUDUSDm', {}).get('enabled') == False
    print(f"   AUDUSDm Status: {'❌ DISABLED' if is_disabled else '✅ ENABLED'}")
    if is_disabled:
        print(f"   Reason: {rs.get('symbol_config', {}).get('AUDUSDm', {}).get('reason', 'N/A')}")

db.close()
