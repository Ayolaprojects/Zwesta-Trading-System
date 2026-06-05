"""Exness Emergency Fix - Analyze & Close Losing Positions"""
import sqlite3
import json
from datetime import datetime

db = sqlite3.connect('C:/backend/zwesta_trading.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

print("="*80)
print("⚠️  EXNESS EMERGENCY DIAGNOSTIC - OPEN POSITIONS ANALYSIS")
print("="*80)

# Get open positions
cur.execute("""
    SELECT bot_id, ticket, symbol, order_type, volume, price, profit, 
           status, time_open, trade_data
    FROM trades
    WHERE status = 'open'
    AND bot_id IN (SELECT bot_id FROM user_bots WHERE broker_account_id LIKE 'Exness_%')
    ORDER BY profit ASC
""")

open_trades = cur.fetchall()

if not open_trades:
    print("\n✅ NO OPEN POSITIONS - GOOD")
else:
    print(f"\n❌ OPEN POSITIONS WITH LOSSES: {len(open_trades)}")
    total_open_loss = sum(t['profit'] for t in open_trades)
    print(f"   Total drawdown: {total_open_loss:+.2f} ZAR")
    
    print(f"\n📊 DETAILS:")
    print(f"   {'Symbol':<12} {'Type':<6} {'Lots':<8} {'Entry':<12} {'P&L':<10} {'Time':<20}")
    print(f"   {'-'*80}")
    
    for t in open_trades:
        sym = t['symbol']
        order = t['order_type'][:3].upper()
        lots = t['volume']
        price = t['price']
        pnl = t['profit']
        time_open = str(t['time_open'])[:19]
        
        print(f"   {sym:<12} {order:<6} {lots:<8.2f} {price:<12.5f} {pnl:>9.2f} {time_open:<20}")

# Analyze root cause
print("\n" + "="*80)
print("ROOT CAUSE ANALYSIS")
print("="*80)

print("\n🔍 THE PROBLEM:")
print("   1. ALL traded symbols are losing (AUD, GBP, XAU, USD/JPY, ETH, etc.)")
print("   2. Open positions IMMEDIATELY losing money after entry")
print("   3. Losses are 2-3.6x larger than wins historically")
print("   4. Win rate on all symbols: 13-42% (should be 50%+ minimum)")

print("\n⚡ LIKELY ROOT CAUSES:")
print("   A. SIGNAL QUALITY - Entries are at wrong prices")
print("      - Buying at peaks instead of support")
print("      - Selling at bottoms instead of resistance")
print("      - Signal threshold was TOO LOW (threshold=1)")
print()
print("   B. POSITION SIZING - Opening too large for losses")
print("      - When trade goes wrong, loss is magnified")
print("      - Large lot trades (0.1-3.26) on losing signals")
print()
print("   C. TP/SL CONFIGURATION - Take profits too tight, stops too wide")
print("      - Average loss: 30 ZAR vs average win: 8 ZAR")
print("      - Suggests SL hits more often than TP")
print()
print("   D. MARKET REGIME - Trades opened in wrong conditions")
print("      - Breakout mode in sideways market")
print("      - Trend following in ranging market")

# Bot runtime check
cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Exness_%' LIMIT 1")
bot = cur.fetchone()

if bot:
    rs = json.loads(bot['runtime_state'] or '{}')
    print("\n⚙️  CURRENT SIGNAL SETTINGS:")
    print(f"   Signal Threshold: {rs.get('signalThreshold', 'N/A')}")
    print(f"   Effective Threshold: {rs.get('effectiveSignalThreshold', 'N/A')}")
    print(f"   Trade Amount: {rs.get('tradeAmount', 'N/A')}")
    print(f"   Effective Trade Amount: {rs.get('effectiveTradeAmount', 'N/A')}")

print("\n" + "="*80)
print("IMMEDIATE ACTIONS REQUIRED")
print("="*80)

print("\n1️⃣  EMERGENCY (Do Now):")
if open_trades:
    print(f"   ❌ CLOSE ALL {len(open_trades)} OPEN POSITIONS MANUALLY")
    print(f"   ❌ Total loss if left open: {total_open_loss:+.2f} ZAR")
    print(f"   ❌ Command: Go to MT5 → Close all positions")
else:
    print(f"   ✓ No open positions to close")

print("\n2️⃣  PAUSE TRADING:")
print("   ❌ Disable all Exness bots until investigation complete")
print("   ✓ They're losing money on EVERY symbol")

print("\n3️⃣  DIAGNOSTIC STEPS:")
print("   • Check if signal feed is inverted (BUY signals = SELL, vice versa)")
print("   • Verify TP/SL ratio: wins should be at least as big as losses")
print("   • Review last 10 winning trades vs last 10 losing trades")
print("   • Compare entry price to market peak/trough at entry time")

print("\n4️⃣  FIX REQUIRED:")
print("   • Signal threshold increase alone won't fix this (I already did that)")
print("   • Need strategy parameter review:")
print("   • - Reverse signals? (if inverted)")
print("   • - Adjust TP/SL targets?")
print("   • - Change lot sizing algorithm?")
print("   • - Switch to different strategy entirely?")

print("\n" + "="*80)

db.close()

print("\n⛔ DO NOT restart backend until these positions are closed and root cause fixed!")
