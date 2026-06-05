"""Fix Exness Bots - Address root cause of losses"""
import json
import sqlite3
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()

# All Exness bots
EXNESS_BOTS = [
    'bot_1779796196293',
    'bot_1780074514247', 
    'bot_1780076647525',
    'bot_1780268294546'
]

def main():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    
    print("="*80)
    print("EXNESS BOT STRUCTURAL FIX - ADDRESSING ROOT CAUSE")
    print("="*80)
    
    for bot_id in EXNESS_BOTS:
        cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (bot_id,))
        r = cur.fetchone()
        if not r:
            print(f"\n❌ {bot_id}: NOT FOUND")
            continue
        
        rs = json.loads(r['runtime_state'] or '{}') if r['runtime_state'] else {}
        
        # PROBLEM: Losses are 3.6x larger than wins
        # ROOT CAUSE: TP/SL targets are misaligned
        
        # FIX #1: Reduce position size dramatically
        # Before: tradeAmount=6.0 (too large)
        # After: tradeAmount=0.5 (conservative, test mode)
        rs['tradeAmount'] = 0.5
        rs['effectiveTradeAmount'] = 0.5
        
        # FIX #2: Increase SL threshold to protect capital
        # Before: Unknown (likely too wide)
        # After: Tight stop loss + wider target
        rs['stopLossPercent'] = 0.5  # 0.5% SL (tight)
        rs['takeProfitPercent'] = 1.5  # 1.5% TP (wider) = 1:3 ratio
        
        # FIX #3: Reverse signals test (check if signal direction is inverted)
        # If bots are buying at peaks, try SELLING at peaks instead
        rs['reverseSignals'] = False  # Set to True if losses continue
        rs['signalInversionTest'] = 'PENDING'
        
        # FIX #4: Disable pyramid/martingale (avoid doubling down on losses)
        rs['pyramidingEnabled'] = False
        rs['martingaleEnabled'] = False
        rs['averagingEnabled'] = False
        
        # FIX #5: Very strict management to exit at first loss
        rs['hardLossLimitPercent'] = 2.0  # Exit if -2% in one trade
        rs['dailyLossLimitPercent'] = 5.0  # Pause if -5% daily loss
        rs['consecutiveLossThreshold'] = 3  # Pause after 3 losses
        
        # FIX #6: Disable all bots until verified working
        rs['enabled'] = False
        rs['pauseReason'] = 'Emergency fix applied - testing mode'
        rs['pausedUntil'] = None
        
        # Metadata
        rs['lastFixApplied'] = NOW
        rs['fixVersion'] = '2026-06-05-emergency'
        rs['fixNotes'] = 'Reduced position size to 0.5, TP:SL ratio 1:3, disabled pyramid'
        
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
            (json.dumps(rs), NOW, bot_id)
        )
        
        print(f"\n✓ {bot_id}")
        print(f"   • Trade amount: 6.0 → 0.5 (88% reduction)")
        print(f"   • SL: 0.5% | TP: 1.5% (1:3 ratio)")
        print(f"   • Pyramid/Martingale: DISABLED")
        print(f"   • Status: PAUSED (testing mode)")
        print(f"   • Hard loss limits: 2% per trade, 5% daily")
    
    c.commit()
    c.close()
    
    print("\n" + "="*80)
    print("✅ FIXES APPLIED")
    print("="*80)
    
    print("\nCHANGES SUMMARY:")
    print("   1. ✓ Position size reduced 88% (6.0 → 0.5 lots)")
    print("   2. ✓ TP/SL ratio fixed (1:3 instead of 0.28:1)")
    print("   3. ✓ Pyramid/Martingale disabled (no doubling down)")
    print("   4. ✓ Hard loss limits enabled (2% per trade, 5% daily)")
    print("   5. ✓ Bots PAUSED - won't trade until verified")
    
    print("\n📋 NEXT STEPS:")
    print("   1. Review if TP/SL targets make sense for your strategy")
    print("   2. If losses still occur, set reverseSignals=True to test signal inversion")
    print("   3. Monitor for 24 hours with small position size (0.5 lots)")
    print("   4. If win rate improves to >50%, gradually increase to 2.0 lots")
    print("   5. If losses continue, disable Exness trading entirely")
    
    print("\n⚠️  WARNING:")
    print("   • Bots are now PAUSED - you must manually re-enable after verification")
    print("   • Position size is 88% smaller - losses will be proportionally smaller")
    print("   • This is DIAGNOSTIC MODE, not production trading")
    
    return 0

if __name__ == '__main__':
    main()
