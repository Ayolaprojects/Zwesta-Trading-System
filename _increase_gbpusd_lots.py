#!/usr/bin/env python3
"""
Increase position sizing for profitable GBPUSDm trades
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\backend\zwesta_trading.db'

def analyze_current_sizing():
    """Show current position sizing configuration"""
    
    print("=" * 80)
    print("📊 CURRENT POSITION SIZING ANALYSIS")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT bot_id, name, runtime_state FROM user_bots")
    all_bots = cur.fetchall()
    
    # Filter for Exness bots
    bots = [(bid, name, rs) for bid, name, rs in all_bots 
            if rs and 'Exness' in json.loads(rs).get('brokerName', '')]
    
    for bot_id, name, runtime_state in bots:
        rs = json.loads(runtime_state or '{}')
        
        print(f"🤖 Bot: {bot_id[:25]}... ({name})")
        print(f"   Symbols: {rs.get('symbols', [])}")
        print(f"   Base Position Size: {rs.get('basePositionSize', 1.0)}")
        print(f"   Effective Position Multiplier: {rs.get('effectivePositionSizeMultiplier', 1.0)}")
        print(f"   Scanner Capital Multiplier: {rs.get('effectiveScannerCapitalMultiplier', 1.0)}")
        
        # Symbol performance
        symbol_perf = rs.get('symbolPerformance', {})
        gbpusd_perf = symbol_perf.get('GBPUSDm', {})
        
        if gbpusd_perf:
            print(f"\n   📈 GBPUSDm Performance:")
            print(f"      Verdict: {gbpusd_perf.get('verdict', 'unknown')}")
            print(f"      Multiplier: {gbpusd_perf.get('multiplier', 1.0)}")
            print(f"      P&L: {gbpusd_perf.get('pnl', 0)} ZAR")
            print(f"      Win Rate: {gbpusd_perf.get('winRate', 0)*100:.1f}%")
            print(f"      Trades: {gbpusd_perf.get('samples', 0)}")
        
        print()
    
    conn.close()

def show_multiplier_options():
    """Explain all the ways to increase position sizing"""
    
    print("=" * 80)
    print("💡 HOW TO INCREASE GBPUSDM POSITION SIZE (LOTS)")
    print("=" * 80)
    print()
    
    print("🎯 OPTION 1: INCREASE BASE POSITION SIZE (Recommended)")
    print("   Current: basePositionSize = 0.01 (very conservative)")
    print("   Recommendation for profitable GBPUSDm:")
    print("      → basePositionSize = 0.02 (2x more lots) ✅ SAFE")
    print("      → basePositionSize = 0.03 (3x more lots) ⚠️ MODERATE")
    print("      → basePositionSize = 0.05 (5x more lots) 🔥 AGGRESSIVE")
    print()
    print("   How it works:")
    print("      - Direct multiplier on ALL position sizes")
    print("      - Applies to BOTH GBPUSDm and XAUUSDm")
    print("      - Simple, predictable, effective")
    print()
    
    print("🎯 OPTION 2: SYMBOL PERFORMANCE MULTIPLIER (Automatic)")
    print("   Current System: CAPPED at 1.1x maximum")
    print("   Problem: Even profitable symbols limited to 10% boost")
    print()
    print("   Backend Code Location: Line 3206")
    print("   Current: size_multiplier *= max(0.7, min(..., 1.1))")
    print("                                           ^^^^ CAPS AT 1.1x")
    print()
    print("   Recommendation: REMOVE CAP to allow up to 1.5x")
    print("   Change to: size_multiplier *= max(0.7, symbol_performance.get('multiplier', 1.0))")
    print("                                        ^^^ REMOVE min(..., 1.1) cap")
    print()
    print("   Result: GBPUSDm with 'favored' verdict → 1.5x position size")
    print()
    
    print("🎯 OPTION 3: SYMBOL-SPECIFIC OVERRIDES (Advanced)")
    print("   Create per-symbol position size overrides in runtime_state:")
    print("   {")
    print("     'symbolPositionSizeOverrides': {")
    print("       'GBPUSDm': 1.5,  # 50% larger positions")
    print("       'XAUUSDm': 0.75  # 25% smaller positions")
    print("     }")
    print("   }")
    print()
    print("   Note: Requires backend code changes to read this field")
    print()
    
    print("🎯 OPTION 4: INCREASE TRADE AMOUNT (Capital-based)")
    print("   Current: System calculates from account balance")
    print("   Alternative: Manually set tradeAmount in runtime_state")
    print()
    print("   Current tradeAmount: ~R50-100 per trade")
    print("   Increase to: R150-200 per trade (more capital per position)")
    print()
    print("   Risk: Uses more capital, higher drawdown if wrong")
    print()

def recommend_approach():
    """Provide specific recommendation"""
    
    print("=" * 80)
    print("✅ RECOMMENDED APPROACH FOR GBPUSDM")
    print("=" * 80)
    print()
    
    print("📊 CURRENT SITUATION:")
    print("   - GBPUSDm: +99 ZAR profit, PF=1.15 ✅ PROVEN PROFITABLE")
    print("   - Account: R1,375 balance")
    print("   - Current position size: 0.01 lots (VERY conservative)")
    print()
    
    print("🎯 STEP-BY-STEP PLAN:")
    print()
    print("   PHASE 1: DOUBLE POSITION SIZE (Conservative) ✅")
    print("   ────────────────────────────────────────────")
    print("   Action: Set basePositionSize = 0.02")
    print("   Impact: 2x more profit per GBPUSDm trade")
    print("   Risk: Moderate (2x drawdown if losing)")
    print("   Timeline: Next 50 trades")
    print()
    
    print("   PHASE 2: REMOVE SYMBOL MULTIPLIER CAP ✅")
    print("   ────────────────────────────────────────")
    print("   Action: Remove 1.1x cap in backend code")
    print("   Impact: GBPUSDm can reach 1.5x when 'favored'")
    print("   Risk: Low (only applies to proven profitable symbols)")
    print("   Timeline: Immediate")
    print()
    
    print("   PHASE 3: INCREASE BASEPOSITIONSIZE FURTHER (if Phase 1 successful)")
    print("   ──────────────────────────────────────────────────────────────────")
    print("   Action: Set basePositionSize = 0.03 or 0.05")
    print("   Impact: 3-5x more profit per trade")
    print("   Risk: Higher drawdown exposure")
    print("   Timeline: After R2,000 account milestone")
    print()
    
    print("⚠️  RISK MANAGEMENT:")
    print("   - Start conservative (0.02 base size)")
    print("   - Monitor next 50 GBPUSDm trades")
    print("   - If PF stays > 1.1 → increase more")
    print("   - If PF drops < 1.0 → revert to 0.01")
    print()
    
    print("💰 EXPECTED RESULTS:")
    print("   Current: 0.01 lots, ~R5-10 profit per GBPUSDm win")
    print("   Phase 1: 0.02 lots, ~R10-20 profit per win (2x)")
    print("   Phase 2: 0.02 lots + 1.5x favored = 0.03 lots, ~R15-30 per win (3x)")
    print("   Phase 3: 0.05 lots + 1.5x favored = 0.075 lots, ~R37-75 per win (7.5x)")
    print()

def create_implementation_scripts():
    """Generate scripts to apply changes"""
    
    # Script 1: Increase base position size
    script1 = """#!/usr/bin/env python3
import sqlite3
import json

DB_PATH = r'C:\\backend\\zwesta_trading.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get all bots
cur.execute("SELECT bot_id, runtime_state FROM user_bots")
all_bots = cur.fetchall()

# Filter for Exness bots
for bot_id, runtime_state in all_bots:
    rs = json.loads(runtime_state or '{}')
    
    # Skip non-Exness bots
    if 'Exness' not in rs.get('brokerName', ''):
        continue
    
    # Increase base position size
    old_size = rs.get('basePositionSize', 0.01)
    new_size = 0.02  # CHANGE THIS VALUE (0.02 = conservative, 0.03 = moderate, 0.05 = aggressive)
    
    rs['basePositionSize'] = new_size
    
    print(f"Bot {bot_id[:25]}...: {old_size} → {new_size}")
    
    cur.execute("UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?", 
               (json.dumps(rs), bot_id))

conn.commit()
conn.close()

print("✅ Base position size updated")
print("⚠️  Restart backend to apply changes")
"""
    
    with open('_increase_position_size.py', 'w', encoding='utf-8') as f:
        f.write(script1)
    
    print("📄 Created: _increase_position_size.py")
    print()
    
    # Script 2: Backend code fix for multiplier cap
    instructions = """
# REMOVE SYMBOL MULTIPLIER CAP - BACKEND CODE CHANGE

📄 File: C:\\backend\\multi_broker_backend_updated.py
📍 Line: ~3206

CURRENT CODE (CAPPED):
────────────────────────────────────────────────────
if symbol_performance:
    size_multiplier *= max(0.7, min(_safe_float(symbol_performance.get('multiplier'), 1.0), 1.1))
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                CAPS AT 1.1x - PREVENTS GBPUSDm FROM REACHING 1.5x

CHANGE TO (UNCAPPED):
────────────────────────────────────────────────────
if symbol_performance:
    symbol_mult = max(0.7, _safe_float(symbol_performance.get('multiplier'), 1.0))
    size_multiplier *= symbol_mult
    # Allow up to 1.5x for 'favored' symbols (removed artificial 1.1x cap)

WHY THIS HELPS:
────────────────────────────────────────────────────
- GBPUSDm with 'favored' verdict can reach 1.5x multiplier
- System already calculates 1.5x based on profitability
- Cap at 1.1x was preventing profitable symbols from scaling up
- Removing cap = more profit from proven winners like GBPUSDm

RISK:
────────────────────────────────────────────────────
- Low risk (only affects profitable symbols)
- System still limits to 1.5x maximum (SYMBOL_PERF_FAVOR_MULT = 1.5)
- Losing symbols still get reduced (0.7x minimum)
"""
    
    with open('REMOVE_MULTIPLIER_CAP.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("📄 Created: REMOVE_MULTIPLIER_CAP.txt")
    print()

def main():
    print("=" * 80)
    print("🚀 INCREASE GBPUSDM POSITION SIZE GUIDE")
    print("=" * 80)
    print()
    
    analyze_current_sizing()
    show_multiplier_options()
    recommend_approach()
    create_implementation_scripts()
    
    print("=" * 80)
    print("✅ GUIDE COMPLETE")
    print("=" * 80)
    print()
    print("📋 NEXT STEPS:")
    print("   1. Review recommended approach above")
    print("   2. Edit _increase_position_size.py (set desired size: 0.02, 0.03, or 0.05)")
    print("   3. Run: python _increase_position_size.py")
    print("   4. Apply backend code change (see REMOVE_MULTIPLIER_CAP.txt)")
    print("   5. Restart backend")
    print("   6. Monitor next 50 GBPUSDm trades")
    print()

if __name__ == "__main__":
    main()
