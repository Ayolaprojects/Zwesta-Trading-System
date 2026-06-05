#!/usr/bin/env python3
"""
Diagnose signal inversion - bot entering opposite direction trades
Flash trades + heavy losses = wrong signal direction
"""

import json

STATUS_FILE = 'bot_status.json'

def check_signal_inversion():
    """Check for signal inversion patterns"""
    
    try:
        with open(STATUS_FILE, 'r') as f:
            data = json.load(f)
    except:
        print("❌ Could not load bot_status.json")
        return
    
    exness_bots = [b for b in data.get('bots', []) if b.get('broker_type') == 'Exness']
    
    print("=" * 70)
    print("SIGNAL INVERSION DIAGNOSTIC")
    print("=" * 70)
    
    for bot in exness_bots:
        bot_id = bot['botId']
        trades = bot.get('totalTrades', 0)
        win_rate = bot.get('winRate', 0)
        profit = bot.get('totalProfit', 0)
        
        print(f"\nBot: {bot_id}")
        print(f"  Total Trades: {trades}")
        print(f"  Win Rate: {win_rate}%")
        print(f"  Total P&L: ${profit:.2f}")
        
        # Red flags for signal inversion
        flags = []
        
        # Flash trades = low win rate + many trades
        if trades > 50 and win_rate < 30:
            flags.append("❌ FLASH TRADING DETECTED (many trades, low win rate)")
        
        # Consistent losses
        if profit < -20:
            flags.append("❌ HEAVY LOSSES (signal likely inverted)")
        
        # No open positions + many losses = wrong direction
        open_pos = bot.get('openPositions', [])
        if len(open_pos) == 0 and profit < -10:
            flags.append("❌ NO POSITIONS HELD + HEAVY LOSSES (closed at loss)")
        
        # Strategy check
        strategy = bot.get('strategy', '')
        print(f"  Strategy: {strategy}")
        
        if flags:
            print("\n  🚨 ISSUES DETECTED:")
            for flag in flags:
                print(f"     {flag}")
            print("\n  💡 LIKELY CAUSE:")
            print("     Bot is entering OPPOSITE direction trades")
            print("     (Buying when should SELL, or vice versa)")
            print("\n  ✅ FIX:")
            print("     1. Delete this bot")
            print("     2. Create new bot with INVERTED signal")
            print("     3. Or use complementary symbol mapping")
        else:
            print("  ✅ No obvious signal inversion")
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    check_signal_inversion()
