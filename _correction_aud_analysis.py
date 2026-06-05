"""Re-evaluate AUDUSDm - correction to optimization"""
import sqlite3
import json
from datetime import datetime, timedelta

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("="*80)
print("CORRECTION: AUDUSDm RE-EVALUATION")
print("="*80)

# Problem: My recent "last 100 trades" analysis showed only 1 AUDUSDm trade (-4.71)
# But full history shows 91 trades with -1217.64 ZAR total loss
# This is a DATA ISSUE in how I filtered

print("\n⚠️  PREVIOUS ANALYSIS ERROR:")
print("   - I only looked at LAST 100 trades database records")
print("   - AUDUSDm appeared only once in that window (-4.71 loss)")
print("   - I incorrectly labeled it '0% win rate'")

print("\n✅ CORRECTED ANALYSIS:")
print("   - Total AUDUSDm trades: 91")
print("   - Win rate: 41.8% (38 wins, 51 losses)")
print("   - Total P&L: -1217.64 ZAR (LOSING)")
print("   - Avg win: +8.49 ZAR")
print("   - Avg loss: -30.20 ZAR (3.6x bigger than wins!)")
print("   - Last 10 trades: 3/10 wins, -1017.14 ZAR")

print("\n📊 VERDICT ON AUDUSDm:")
print("   ❌ Despite potential, AUDUSDm is actually LOSING money")
print("   ❌ Losses are 3.6x larger than wins")
print("   ❌ Recent performance is worse (only 30% last 10)")
print("   ❌ Should REMAIN DISABLED")

# Now check other symbols
print("\n" + "="*80)
print("COMPREHENSIVE SYMBOL ANALYSIS")
print("="*80)

symbols_to_check = ['USDJPYm', 'GBPUSDm', 'XAUUSDm', 'ETHUSDm', 'USTECm']

for symbol in symbols_to_check:
    cur.execute("""
        SELECT profit FROM trades WHERE symbol = ?
        ORDER BY time_open DESC
        LIMIT 100
    """, (symbol,))
    
    trades = cur.fetchall()
    if not trades:
        print(f"\n{symbol}: No recent trades")
        continue
    
    profits = [t['profit'] for t in trades]
    total = sum(profits)
    wins = len([p for p in profits if p > 0])
    losses = len([p for p in profits if p < 0])
    
    win_rate = (wins / len(profits) * 100) if profits else 0
    avg_win = sum([p for p in profits if p > 0]) / wins if wins > 0 else 0
    avg_loss = sum([p for p in profits if p < 0]) / losses if losses > 0 else 0
    
    status = "✅" if total > 0 and win_rate > 50 else "⚠️ " if total > -50 else "❌"
    
    print(f"\n{symbol}: {status}")
    print(f"   Trades: {len(profits)} | Win rate: {win_rate:.0f}% | P&L: {total:+.2f}")
    if avg_win or avg_loss:
        print(f"   Avg win: {avg_win:+.2f} | Avg loss: {avg_loss:+.2f} | Ratio: {abs(avg_win/avg_loss) if avg_loss else 0:.2f}x")

db.close()

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)
print("\n✓ KEEP AUDUSDm DISABLED - it's actually losing -1217.64 ZAR overall")
print("✓ Focus on profitable symbols: XAUUSDm, GBPUSDm")
print("✓ Re-check USDJPYm for large loss patterns (-33.46 in your recent data)")
print("\nNote: 'Usually profitable' in forex depends on market conditions.")
print("Current bot data shows consistent losses, not profits.")
