#!/usr/bin/env python3
"""
Show 10x multiplier impact on GBPUSDm profits
"""

def show_10x_impact():
    print("=" * 80)
    print("🚀 10X MULTIPLIER ON PROFITABLE GBPUSDM - IMPACT ANALYSIS")
    print("=" * 80)
    print()
    
    print("✅ CHANGES APPLIED:")
    print("   - SYMBOL_PERF_FAVOR_MULT: 1.5x → 10x")
    print("   - Overall size_multiplier cap: 1.8x → 12x")
    print("   - Allows: 1.2 (high quality) × 10 (favored symbol) = 12x total")
    print()
    
    print("=" * 80)
    print("💰 PROFIT PROJECTIONS WITH 10X MULTIPLIER")
    print("=" * 80)
    print()
    
    scenarios = [
        {
            'name': 'CONSERVATIVE',
            'base': 0.01,
            'symbol_mult': 10.0,
            'quality_mult': 1.0,
            'description': 'Start small, let system scale automatically'
        },
        {
            'name': 'MODERATE',
            'base': 0.02,
            'symbol_mult': 10.0,
            'quality_mult': 1.0,
            'description': 'Double base + 10x symbol = 20x total scaling'
        },
        {
            'name': 'AGGRESSIVE',
            'base': 0.05,
            'symbol_mult': 10.0,
            'quality_mult': 1.0,
            'description': '5x base + 10x symbol = 50x total scaling'
        },
        {
            'name': 'MAXIMUM',
            'base': 0.10,
            'symbol_mult': 10.0,
            'quality_mult': 1.2,
            'description': '10x base + 10x symbol + 1.2 quality = 120x!'
        }
    ]
    
    for scenario in scenarios:
        final_lots = scenario['base'] * scenario['symbol_mult'] * scenario['quality_mult']
        
        # Estimate profits
        # Current: 0.01 lots = ~R7 per win, ~R4 per loss
        # Scale proportionally
        profit_per_win = 7 * (final_lots / 0.01)
        loss_per_loss = 4 * (final_lots / 0.01)
        
        # 50 trades at 42% WR
        wins = 21
        losses = 29
        net_50_trades = (wins * profit_per_win) - (losses * loss_per_loss)
        
        print(f"📊 {scenario['name']} SCENARIO:")
        print(f"   Base: {scenario['base']} lots")
        print(f"   Symbol Multiplier: {scenario['symbol_mult']}x (GBPUSDm favored)")
        print(f"   Quality Multiplier: {scenario['quality_mult']}x")
        print(f"   → Final Position: {final_lots:.3f} lots ({final_lots/0.01:.0f}x original)")
        print()
        print(f"   Per Trade:")
        print(f"      Win: +R{profit_per_win:.0f} (vs R7 currently)")
        print(f"      Loss: -R{loss_per_loss:.0f} (vs R4 currently)")
        print()
        print(f"   50 GBPUSDm Trades (42% WR):")
        print(f"      Net Profit: +R{net_50_trades:.0f}")
        print(f"      vs Current: +R18 (50 trades at 0.01 lots)")
        print(f"      Improvement: {net_50_trades/18:.0f}x MORE PROFIT")
        print()
        print(f"   💡 {scenario['description']}")
        print()
        print("-" * 80)
        print()
    
    print()
    print("=" * 80)
    print("⚠️ CRITICAL RISK WARNINGS")
    print("=" * 80)
    print()
    
    print("🔴 10X MULTIPLIER = 10X DRAWDOWN TOO!")
    print()
    print("   If GBPUSDm has a losing streak:")
    print()
    print("   Current (0.01 lots):")
    print("      5 consecutive losses = -R20")
    print("      10 consecutive losses = -R40")
    print("      ✅ Manageable on R1,375 account")
    print()
    print("   With 0.05 base + 10x symbol (0.5 lots):")
    print("      5 consecutive losses = -R1,000")
    print("      10 consecutive losses = -R2,000")
    print("      ❌ CATASTROPHIC - Wipes out entire account!")
    print()
    print("   With 0.10 base + 10x symbol (1.0 lots):")
    print("      5 consecutive losses = -R2,000")
    print("      10 consecutive losses = -R4,000")
    print("      💀 ACCOUNT DESTROYED - Goes negative!")
    print()
    
    print("🟡 MANDATORY RISK CONTROLS:")
    print()
    print("   1. MAX DAILY LOSS LIMIT:")
    print("      Set maxDailyLoss = 5% (R68 on R1,375 account)")
    print("      System auto-pauses if hit")
    print()
    print("   2. MAX CONSECUTIVE LOSSES:")
    print("      After 3 losses, reduce multiplier to 1.0x")
    print("      After 5 losses, pause trading for 24h")
    print()
    print("   3. ACCOUNT SIZE REQUIREMENTS:")
    print("      0.01 base + 10x: Minimum R500 account ✅")
    print("      0.02 base + 10x: Minimum R1,000 account ✅")
    print("      0.05 base + 10x: Minimum R5,000 account ❌ (you have R1,375)")
    print("      0.10 base + 10x: Minimum R10,000 account ❌")
    print()
    print("   4. GRADUAL SCALING:")
    print("      Week 1: 0.01 base + 10x symbol = 0.1 lots max")
    print("      Week 2: If PF > 1.1, increase to 0.02 base")
    print("      Month 1: If account > R2,000, increase to 0.03 base")
    print("      Month 2: If account > R5,000, increase to 0.05 base")
    print()
    
    print("=" * 80)
    print("✅ RECOMMENDED APPROACH (SAFE 10X)")
    print("=" * 80)
    print()
    
    print("🎯 PHASE 1: START WITH 0.01 BASE + 10X SYMBOL")
    print()
    print("   Position Size: 0.01 × 10 = 0.1 lots")
    print("   Profit per win: +R70 (vs R7 currently)")
    print("   Loss per loss: -R40 (vs R4 currently)")
    print("   50 trades net: +R180 (vs R18 currently) = 10x more profit")
    print()
    print("   Risk Profile:")
    print("      5 losses = -R200 (14.5% drawdown) ⚠️ Manageable")
    print("      10 losses = -R400 (29% drawdown) 🔴 Painful but survivable")
    print()
    print("   ✅ SAFE: R1,375 account can handle this")
    print()
    
    print("🎯 PHASE 2: INCREASE TO 0.02 BASE (AFTER 50 SUCCESSFUL TRADES)")
    print()
    print("   Position Size: 0.02 × 10 = 0.2 lots")
    print("   Profit per win: +R140")
    print("   50 trades net: +R360 = 20x more profit than current")
    print()
    print("   Risk Profile:")
    print("      5 losses = -R400 (29% drawdown on R1,375)")
    print("      ⚠️ REQUIRES: Account > R2,000 to be safe")
    print()
    
    print("🎯 PHASE 3: SCALE UP AS ACCOUNT GROWS")
    print()
    print("   R2,000 account → 0.02 base (0.2 lots max)")
    print("   R5,000 account → 0.05 base (0.5 lots max)")
    print("   R10,000 account → 0.10 base (1.0 lots max)")
    print()
    
    print("=" * 80)
    print("💡 FINAL RECOMMENDATION")
    print("=" * 80)
    print()
    
    print("✅ START: basePositionSize = 0.01 (keep current)")
    print("   - Let 10x symbol multiplier do the work")
    print("   - 0.01 × 10 = 0.1 lots on GBPUSDm")
    print("   - 10x more profit, manageable risk")
    print()
    print("✅ MONITOR: Next 50 GBPUSDm trades")
    print("   - If PF stays > 1.1: SUCCESS!")
    print("   - If 5+ consecutive losses: PAUSE and review")
    print("   - If account grows to R2,000: Increase to 0.02 base")
    print()
    print("⚠️ AVOID: Jumping straight to 0.05 or 0.10 base")
    print("   - Too risky for R1,375 account")
    print("   - One bad streak = account blown")
    print("   - Build up gradually as account grows")
    print()
    
    print("=" * 80)
    print("📋 IMPLEMENTATION CHECKLIST")
    print("=" * 80)
    print()
    print("   [x] ✅ Backend updated: SYMBOL_PERF_FAVOR_MULT = 10.0")
    print("   [x] ✅ Size cap increased: 1.8x → 12.0x")
    print("   [ ] ⏳ Keep basePositionSize = 0.01 (or run _increase_position_size.py)")
    print("   [ ] ⏳ Restart backend to load changes")
    print("   [ ] ⏳ Enable MT5 AutoTrading")
    print("   [ ] ⏳ Set maxDailyLoss = 5% in bot config")
    print("   [ ] ⏳ Monitor first 10 GBPUSDm trades closely")
    print("   [ ] ⏳ Track drawdown (alert if > 10% account)")
    print()
    
    print("=" * 80)
    print("🚀 EXPECTED RESULTS (0.01 BASE + 10X SYMBOL)")
    print("=" * 80)
    print()
    print("   Current Performance:")
    print("      50 GBPUSDm trades = +R18 net profit")
    print("      Monthly = ~R36-54")
    print("      Time to R2,000 = 12-18 months")
    print()
    print("   With 10x Multiplier:")
    print("      50 GBPUSDm trades = +R180 net profit")
    print("      Monthly = ~R360-540")
    print("      Time to R2,000 = 1-2 months! 🎉")
    print()
    print("   ⚠️ BUT ONLY IF:")
    print("      - GBPUSDm maintains PF > 1.1")
    print("      - No catastrophic losing streaks")
    print("      - Proper risk management in place")
    print()

if __name__ == "__main__":
    show_10x_impact()
