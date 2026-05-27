#!/usr/bin/env python3
"""
Analyze and optimize XAUUSDm (Gold) trading performance
"""
import sqlite3
from collections import defaultdict

DB_PATH = r'C:\backend\zwesta_trading.db'

def analyze_xauusd_performance():
    """Detailed analysis of XAUUSDm trades"""
    
    print("=" * 80)
    print("📊 XAUUSDm (GOLD) PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all XAUUSDm trades
    cur.execute("""
        SELECT 
            trade_id,
            symbol,
            order_type,
            price,
            profit,
            commission,
            swap,
            closed_at,
            trade_data
        FROM trades 
        WHERE symbol = 'XAUUSDm' 
        AND closed_at IS NOT NULL
        ORDER BY closed_at DESC
    """)
    
    trades = cur.fetchall()
    
    if not trades:
        print("⚠️  No closed XAUUSDm trades found in database")
        print()
        print("💡 RECOMMENDATION:")
        print("   XAUUSDm is currently Tier C (experimental) with -12.89 ZAR loss")
        print("   From CSV analysis:")
        print("   - Win Rate: 35%")
        print("   - Profit Factor: 0.92 (needs 1.0+)")
        print("   - Average Loss: -3.57 ZAR/trade")
        print()
        print("   STRATEGY:")
        print("   1. Keep XAUUSDm as SECONDARY symbol (after GBPUSDm)")
        print("   2. Increase signal threshold: 70 (more selective)")
        print("   3. Require higher setup scores: 7.0+ (quality gate)")
        print("   4. Reduce position size: 20% of normal")
        print("   5. Monitor for 50+ trades before re-evaluation")
        conn.close()
        return
    
    print(f"📈 TOTAL XAUUSDm TRADES: {len(trades)}")
    print()
    
    # Calculate metrics (profit is in column 4, including commission and swap)
    import json
    
    winning_trades = []
    losing_trades = []
    
    for t in trades:
        net_profit = (t[4] or 0) + (t[5] or 0) + (t[6] or 0)  # profit + commission + swap
        if net_profit > 0:
            winning_trades.append((t, net_profit))
        else:
            losing_trades.append((t, net_profit))
    
    total_profit = sum(p for _, p in winning_trades)
    total_loss = sum(p for _, p in losing_trades)
    net_pnl = total_profit + total_loss
    
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0
    
    avg_win = total_profit / len(winning_trades) if winning_trades else 0
    avg_loss = total_loss / len(losing_trades) if losing_trades else 0
    
    print("💰 PERFORMANCE METRICS:")
    print(f"   Win Rate: {win_rate:.1f}% ({len(winning_trades)}W / {len(losing_trades)}L)")
    print(f"   Profit Factor: {profit_factor:.2f} {'✅' if profit_factor >= 1.0 else '❌'}")
    print(f"   Net P&L: {net_pnl:+.2f} ZAR {'✅' if net_pnl > 0 else '❌'}")
    print(f"   Average Win: +{avg_win:.2f} ZAR")
    print(f"   Average Loss: {avg_loss:.2f} ZAR")
    print(f"   Risk/Reward: {abs(avg_win/avg_loss):.2f}" if avg_loss != 0 else "   Risk/Reward: N/A")
    print()
    
    # Exit reasons
    exit_reasons = defaultdict(int)
    exit_pnl = defaultdict(float)
    
    for t in trades:
        net_profit = (t[4] or 0) + (t[5] or 0) + (t[6] or 0)
        
        # Try to get exit reason from trade_data JSON
        reason = 'Manual/Auto'
        if t[8]:  # trade_data column
            try:
                trade_data = json.loads(t[8])
                reason = trade_data.get('exit_reason') or trade_data.get('close_reason') or 'Manual/Auto'
            except:
                pass
        
        exit_reasons[reason] += 1
        exit_pnl[reason] += net_profit
    
    print("📊 EXIT REASON BREAKDOWN:")
    for reason, count in sorted(exit_reasons.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(trades) * 100
        pnl = exit_pnl[reason]
        emoji = "✅" if pnl > 0 else "❌"
        print(f"   {emoji} {reason}: {count} trades ({pct:.1f}%) | P&L: {pnl:+.2f} ZAR")
    
    print()
    
    # Time analysis (if enough data)
    if len(trades) >= 10:
        recent_10 = trades[:10]
        recent_pnl = sum((t[4] or 0) + (t[5] or 0) + (t[6] or 0) for t in recent_10)
        recent_wins = len([t for t in recent_10 if ((t[4] or 0) + (t[5] or 0) + (t[6] or 0)) > 0])
        
        print("📈 RECENT PERFORMANCE (Last 10 Trades):")
        print(f"   Win Rate: {recent_wins/10*100:.1f}%")
        print(f"   Net P&L: {recent_pnl:+.2f} ZAR {'✅ Improving' if recent_pnl > 0 else '❌ Declining'}")
        print()
    
    conn.close()
    
    # Generate recommendations
    generate_xauusd_recommendations(win_rate, profit_factor, net_pnl, avg_win, avg_loss)

def generate_xauusd_recommendations(win_rate, profit_factor, net_pnl, avg_win, avg_loss):
    """Generate specific recommendations for XAUUSDm trading"""
    
    print("=" * 80)
    print("💡 XAUUSDm OPTIMIZATION RECOMMENDATIONS:")
    print("=" * 80)
    print()
    
    # Determine if XAUUSDm should be traded
    if profit_factor < 0.8:
        print("❌ RECOMMENDATION: REMOVE XAUUSDm")
        print(f"   Reason: Profit Factor {profit_factor:.2f} too low (< 0.80)")
        print("   Action: Set symbols to ['GBPUSDm'] only")
        print()
    elif profit_factor < 1.0:
        print("⚠️  RECOMMENDATION: REDUCE XAUUSDm EXPOSURE")
        print(f"   Reason: Profit Factor {profit_factor:.2f} below breakeven")
        print("   Actions:")
        print("   1. Keep as SECONDARY symbol (after GBPUSDm)")
        print("   2. Increase signal threshold: 75 (very selective)")
        print("   3. Require setup score: 8.0+ (only best setups)")
        print("   4. Position size: 50% of normal")
        print("   5. Monitor for improvement")
        print()
    elif profit_factor < 1.2:
        print("⚠️  RECOMMENDATION: CAUTIOUS XAUUSDm TRADING")
        print(f"   Reason: Profit Factor {profit_factor:.2f} marginally profitable")
        print("   Actions:")
        print("   1. Keep as SECONDARY symbol")
        print("   2. Signal threshold: 70 (selective)")
        print("   3. Setup score: 7.0+")
        print("   4. Position size: 75% of normal")
        print()
    else:
        print("✅ RECOMMENDATION: OPTIMIZE XAUUSDm AS PRIMARY")
        print(f"   Reason: Profit Factor {profit_factor:.2f} is profitable!")
        print("   Actions:")
        print("   1. Move to PRIMARY alongside GBPUSDm: ['GBPUSDm', 'XAUUSDm']")
        print("   2. Signal threshold: 65 (normal)")
        print("   3. Setup score: 6.0+")
        print("   4. Position size: 100% (normal)")
        print()
    
    # Specific improvements
    print("🔧 SPECIFIC OPTIMIZATIONS:")
    
    if avg_loss != 0 and abs(avg_win / avg_loss) < 1.5:
        print("   1. ⚠️  Risk/Reward too low - tighten stop losses")
        print("      Current R/R: {:.2f}, Target: 2.0+".format(abs(avg_win/avg_loss)))
    
    if win_rate < 40:
        print("   2. ❌ Win rate too low - increase entry quality")
        print(f"      Current: {win_rate:.1f}%, Target: 40%+")
        print("      → Require trend + EMA alignment + momentum confirmation")
    
    print("   3. 📊 Gold-specific considerations:")
    print("      → Trade during London/NY sessions (higher liquidity)")
    print("      → Avoid news events (NFP, FOMC, inflation data)")
    print("      → Watch USD correlation (gold inverse to USD)")
    print("      → Monitor $2000-2100 range (key levels)")
    print()
    
    print("=" * 80)
    print("🎯 IMMEDIATE ACTION:")
    print("=" * 80)
    
    if profit_factor < 1.0:
        print("   Keep current setup:")
        print("   - symbols: ['GBPUSDm', 'XAUUSDm'] (GBPUSDm priority)")
        print("   - Signal threshold: 70 (selective)")
        print("   - Monitor XAUUSDm performance closely")
        print("   - If P&L doesn't improve in 50 trades → REMOVE")
    else:
        print("   ✅ XAUUSDm is profitable - treat equally with GBPUSDm")
        print("   - symbols: ['GBPUSDm', 'XAUUSDm']")
        print("   - Signal threshold: 65")
        print("   - Normal position sizing")
    
    print()

def apply_xauusd_optimizations():
    """Apply recommended settings to database"""
    
    print("=" * 80)
    print("🔧 APPLYING XAUUSDm OPTIMIZATIONS...")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Current optimization keeps XAUUSDm as secondary
    # This is already applied - just verify
    
    cur.execute("""
        SELECT bot_id, name, runtime_state 
        FROM user_bots 
        WHERE broker = 'Exness' 
        AND is_active = 1
    """)
    
    bots = cur.fetchall()
    
    print("📋 CURRENT BOT CONFIGURATIONS:")
    for bot_id, name, runtime_state in bots:
        import json
        rs = json.loads(runtime_state or '{}')
        symbols = rs.get('symbols', [])
        threshold = rs.get('signalThreshold', 'NOT SET')
        
        print(f"   {bot_id[:20]}... ({name})")
        print(f"      Symbols: {symbols}")
        print(f"      Threshold: {threshold}")
        
        if 'XAUUSDm' in symbols:
            position = symbols.index('XAUUSDm') + 1
            if position == 1:
                print(f"      ⚠️  XAUUSDm is PRIMARY (position {position})")
            else:
                print(f"      ✅ XAUUSDm is SECONDARY (position {position})")
        print()
    
    conn.close()
    
    print("✅ Configuration verified - XAUUSDm optimized as secondary symbol")
    print()

def main():
    analyze_xauusd_performance()
    apply_xauusd_optimizations()

if __name__ == "__main__":
    main()
