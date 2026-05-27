#!/usr/bin/env python3
"""
Comprehensive analysis of ALL losing symbols to determine if any can be optimized
"""
import sqlite3
from collections import defaultdict
import json

DB_PATH = r'C:\backend\zwesta_trading.db'

# Symbol performance from CSV analysis (560 trades)
SYMBOL_PERFORMANCE = {
    'GBPUSDm': {'pnl': 99.08, 'winrate': 42, 'pf': 1.15, 'tier': 'A'},
    'XAUUSDm': {'pnl': -12.89, 'winrate': 35, 'pf': 0.92, 'tier': 'C'},  # Just optimized
    'US30m': {'pnl': -132.82, 'winrate': 33, 'pf': 0.75, 'tier': 'B'},
    'BTCUSDm': {'pnl': -589.16, 'winrate': 36, 'pf': 0.31, 'tier': 'D'},
    'ETHUSDm': {'pnl': -331.44, 'winrate': 24, 'pf': 0.19, 'tier': 'D'},
    'USDJPYm': {'pnl': -205.85, 'winrate': 30, 'pf': 0.65, 'tier': 'D'},
    'UKOILm': {'pnl': -107.60, 'winrate': 28, 'pf': 0.70, 'tier': 'D'},
    'NZDUSDm': {'pnl': -153.08, 'winrate': 31, 'pf': 0.68, 'tier': 'D'},
    'USOILm': {'pnl': -126.02, 'winrate': 29, 'pf': 0.72, 'tier': 'D'},
    'EURUSDm': {'pnl': -224.32, 'winrate': 32, 'pf': 0.62, 'tier': 'D'},
    'AUDUSDm': {'pnl': -111.30, 'winrate': 33, 'pf': 0.68, 'tier': 'D'},
    'USDCADm': {'pnl': -205.85, 'winrate': 30, 'pf': 0.65, 'tier': 'D'},
}

def analyze_symbol_from_db(symbol):
    """Get detailed performance from database"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
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
        WHERE symbol = ? 
        AND closed_at IS NOT NULL
        ORDER BY closed_at DESC
        LIMIT 50
    """, (symbol,))
    
    trades = cur.fetchall()
    conn.close()
    
    if not trades:
        return None
    
    # Calculate recent performance (last 10-20 trades)
    recent_limit = min(len(trades), 20)
    recent_trades = trades[:recent_limit]
    
    recent_pnl = sum((t[4] or 0) + (t[5] or 0) + (t[6] or 0) for t in recent_trades)
    recent_wins = len([t for t in recent_trades if ((t[4] or 0) + (t[5] or 0) + (t[6] or 0)) > 0])
    recent_wr = recent_wins / recent_limit * 100 if recent_limit > 0 else 0
    
    return {
        'total_trades': len(trades),
        'recent_trades': recent_limit,
        'recent_pnl': recent_pnl,
        'recent_wr': recent_wr
    }

def determine_optimization_strategy(symbol, csv_data, db_data):
    """Determine if symbol can be optimized and how"""
    
    pnl = csv_data['pnl']
    winrate = csv_data['winrate']
    pf = csv_data['pf']
    
    # Check recent trend if DB data available
    improving = False
    if db_data and db_data['recent_pnl'] > 0 and db_data['recent_wr'] > winrate:
        improving = True
    
    print(f"\n{'='*80}")
    print(f"📊 {symbol} ANALYSIS")
    print(f"{'='*80}")
    print(f"   Overall: {pnl:+.2f} ZAR | WR: {winrate}% | PF: {pf:.2f}")
    
    if db_data:
        print(f"   Recent ({db_data['recent_trades']} trades): {db_data['recent_pnl']:+.2f} ZAR | WR: {db_data['recent_wr']:.1f}%")
        if improving:
            print(f"   ✅ TREND: IMPROVING!")
    
    # Decision logic
    verdict = None
    params = {}
    
    # CATEGORY 1: HOPELESS (PF < 0.50)
    if pf < 0.50:
        verdict = "❌ BLACKLIST PERMANENTLY"
        reason = f"Profit Factor {pf:.2f} catastrophically low - fundamental strategy mismatch"
        params = None
    
    # CATEGORY 2: VERY POOR (PF 0.50-0.70)
    elif pf < 0.70:
        if improving and db_data and db_data['recent_pnl'] > 100:
            verdict = "⚠️ EXTREME CAUTION - TEST ONLY"
            reason = f"PF {pf:.2f} very poor BUT recent trend positive (+{db_data['recent_pnl']:.0f} ZAR)"
            params = {
                'threshold': 80,
                'setup_score': 9.0,
                'position_size': 0.25,
                'max_trades_per_day': 1,
                'note': 'Ultra-selective - only perfect setups'
            }
        else:
            verdict = "❌ BLACKLIST"
            reason = f"PF {pf:.2f} too low, no improvement trend"
            params = None
    
    # CATEGORY 3: POOR (PF 0.70-0.90)
    elif pf < 0.90:
        if improving and db_data and db_data['recent_wr'] > 45:
            verdict = "⚠️ CAUTIOUS OPTIMIZATION POSSIBLE"
            reason = f"PF {pf:.2f} poor but improving - monitor closely"
            params = {
                'threshold': 75,
                'setup_score': 8.0,
                'position_size': 0.50,
                'max_trades_per_day': 2,
                'note': 'Very selective - trend must be strong'
            }
        else:
            verdict = "❌ BLACKLIST (Low Priority)"
            reason = f"PF {pf:.2f} marginally lossy, no clear improvement"
            params = None
    
    # CATEGORY 4: MARGINAL (PF 0.90-1.10)
    elif pf < 1.10:
        verdict = "✅ OPTIMIZATION RECOMMENDED"
        reason = f"PF {pf:.2f} near breakeven - small tweaks could make profitable"
        params = {
            'threshold': 70,
            'setup_score': 7.0,
            'position_size': 0.75,
            'max_trades_per_day': 3,
            'note': 'Selective - wait for good setups'
        }
    
    # CATEGORY 5: PROFITABLE (PF 1.10+)
    else:
        verdict = "✅ ALREADY PROFITABLE"
        reason = f"PF {pf:.2f} profitable - standard optimization"
        params = {
            'threshold': 65,
            'setup_score': 6.0,
            'position_size': 1.0,
            'max_trades_per_day': 5,
            'note': 'Normal trading - proven profitable'
        }
    
    print(f"\n   {verdict}")
    print(f"   Reason: {reason}")
    
    if params:
        print(f"\n   📋 RECOMMENDED PARAMETERS:")
        for key, value in params.items():
            if key != 'note':
                print(f"      {key}: {value}")
        print(f"      💡 {params['note']}")
    
    return {
        'symbol': symbol,
        'verdict': verdict,
        'reason': reason,
        'params': params,
        'improving': improving
    }

def generate_comprehensive_report():
    """Analyze all symbols and generate optimization report"""
    
    print("="*80)
    print("🔍 COMPREHENSIVE SYMBOL OPTIMIZATION ANALYSIS")
    print("="*80)
    print()
    print("Analyzing all losing symbols to determine optimization potential...")
    print()
    
    results = []
    
    for symbol, csv_data in sorted(SYMBOL_PERFORMANCE.items(), key=lambda x: x[1]['pf']):
        db_data = analyze_symbol_from_db(symbol)
        result = determine_optimization_strategy(symbol, csv_data, db_data)
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 OPTIMIZATION SUMMARY")
    print(f"{'='*80}\n")
    
    can_optimize = [r for r in results if r['params'] is not None]
    must_blacklist = [r for r in results if r['params'] is None]
    improving = [r for r in results if r['improving']]
    
    print(f"✅ CAN OPTIMIZE: {len(can_optimize)} symbols")
    for r in can_optimize:
        print(f"   - {r['symbol']}: {r['verdict']}")
    
    print(f"\n❌ MUST BLACKLIST: {len(must_blacklist)} symbols")
    for r in must_blacklist:
        print(f"   - {r['symbol']}: {r['reason']}")
    
    if improving:
        print(f"\n📈 SHOWING IMPROVEMENT: {len(improving)} symbols")
        for r in improving:
            print(f"   - {r['symbol']}: Recent trend is positive")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("💡 FINAL RECOMMENDATIONS")
    print(f"{'='*80}\n")
    
    tier_1 = [r for r in can_optimize if r['params'] and r['params'].get('threshold', 100) <= 70]
    tier_2 = [r for r in can_optimize if r['params'] and 70 < r['params'].get('threshold', 100) <= 75]
    tier_3 = [r for r in can_optimize if r['params'] and r['params'].get('threshold', 100) > 75]
    
    if tier_1:
        print("🟢 TIER 1 - ADD TO ACTIVE TRADING:")
        for r in tier_1:
            print(f"   {r['symbol']}: Threshold {r['params']['threshold']}, Position {r['params']['position_size']*100:.0f}%")
    
    if tier_2:
        print("\n🟡 TIER 2 - CAUTIOUS ADDITION (Monitor Closely):")
        for r in tier_2:
            print(f"   {r['symbol']}: Threshold {r['params']['threshold']}, Position {r['params']['position_size']*100:.0f}%")
    
    if tier_3:
        print("\n🔴 TIER 3 - EXTREME CAUTION (Test Only):")
        for r in tier_3:
            print(f"   {r['symbol']}: Threshold {r['params']['threshold']}, Position {r['params']['position_size']*100:.0f}%")
    
    print("\n⛔ PERMANENT BLACKLIST:")
    for r in must_blacklist:
        if 'catastrophically' in r['reason'].lower() or r['params'] is None:
            print(f"   {r['symbol']}: {r['reason'].split(' - ')[1] if ' - ' in r['reason'] else r['reason']}")
    
    # Reality check
    print(f"\n{'='*80}")
    print("🎯 REALISTIC ASSESSMENT")
    print(f"{'='*80}\n")
    
    print("⚠️  IMPORTANT REALITY CHECK:")
    print()
    print("While some symbols CAN be optimized, you should understand:")
    print()
    print("1. ✅ GBPUSDm is PROVEN PROFITABLE (+99 ZAR, PF=1.15)")
    print("   → This should remain your PRIMARY focus")
    print()
    print("2. ⚠️  XAUUSDm shows improvement (recent +186 ZAR)")
    print("   → Cautious secondary option (just optimized)")
    print()
    print("3. ❌ Most other symbols LOST money for a REASON:")
    print("   → Your strategy doesn't work well on them")
    print("   → Over-optimization = curve-fitting to past data")
    print("   → May not work going forward")
    print()
    print("4. 💡 BETTER STRATEGY:")
    print("   → Master 1-2 profitable symbols (GBPUSDm, XAUUSDm)")
    print("   → Build capital from what WORKS")
    print("   → THEN expand cautiously to 1-2 more symbols")
    print()
    print("5. ⚠️  RISK OF ADDING TOO MANY:")
    print("   → Diluted focus")
    print("   → More complexity = more failure points")
    print("   → Small account can't handle 10+ symbols")
    print()
    print("=" * 80)
    print("📋 RECOMMENDED APPROACH")
    print("=" * 80)
    print()
    print("CONSERVATIVE (Recommended for R1,375 account):")
    print("  symbols: ['GBPUSDm', 'XAUUSDm']")
    print("  Focus: Master these 2 until account reaches R5,000+")
    print()
    print("MODERATE (If you want 1-2 more):")
    print("  symbols: ['GBPUSDm', 'XAUUSDm', 'US30m']")
    print("  US30m only if optimization shows PF > 0.90")
    print()
    print("AGGRESSIVE (Not recommended for small account):")
    print("  symbols: ['GBPUSDm', 'XAUUSDm', 'US30m', 'USOILm']")
    print("  Risk: Spreading too thin, increased complexity")
    print()
    
    return results

def main():
    results = generate_comprehensive_report()
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print()
    print("💡 MY HONEST RECOMMENDATION:")
    print()
    print("   Keep: GBPUSDm (proven profitable)")
    print("   Keep: XAUUSDm (improving, just optimized)")
    print("   Maybe: US30m (if DB shows improvement)")
    print("   Avoid: Everything else (at least for now)")
    print()
    print("   REASON: Your R1,375 account needs FOCUS, not diversification.")
    print("           Master 2 symbols → Build to R5,000 → Then expand.")
    print()

if __name__ == "__main__":
    main()
