#!/usr/bin/env python3
"""
Add daily loss limits and profit protection to all Binance bots
"""

import json
import shutil
from datetime import datetime

STATUS_FILE = 'bot_status.json'

# Safe defaults for Binance (small account)
DAILY_LOSS_LIMIT = 15.0  # Stop trading after $15 loss (25% of account)
PROFIT_LOCK = 5.0  # Lock profits at $5
PROFIT_LOCK_ACTIVATION = 3.0  # Activate when $3 profit reached
DRAWDOWN_PAUSE_PERCENT = 3.0  # Pause at 3% drawdown (tight for small account)
DRAWDOWN_PAUSE_HOURS = 6.0  # Resume after 6 hours

def add_binance_safety_limits():
    """Add daily loss limits to all Binance bots"""
    
    # Backup
    backup = f"{STATUS_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(STATUS_FILE, backup)
    print(f"💾 Backed up to: {backup}\n")
    
    # Load bots
    with open(STATUS_FILE, 'r') as f:
        data = json.load(f)
    
    binance_bots = [b for b in data.get('bots', []) if b.get('broker_type') == 'Binance']
    
    print(f"{'=' * 60}")
    print(f"ADDING DAILY LOSS LIMITS TO BINANCE BOTS")
    print(f"{'=' * 60}\n")
    
    for bot in binance_bots:
        bot_id = bot['botId']
        
        # Set safety limits
        bot['maxDailyLoss'] = DAILY_LOSS_LIMIT
        bot['profitLock'] = PROFIT_LOCK
        bot['drawdownPausePercent'] = DRAWDOWN_PAUSE_PERCENT
        bot['drawdownPauseHours'] = DRAWDOWN_PAUSE_HOURS
        
        # Also update profit protection config if it exists
        if 'profitProtection' not in bot or not bot['profitProtection']:
            bot['profitProtection'] = {
                'enabled': True,
                'activationPercent': 3.0,
                'activationMinProfit': PROFIT_LOCK_ACTIVATION,
                'retraceClosePercent': 5.0,  # Close at 95% of peak (aggressive for small account)
                'switchOnReversal': True,
                'breakEvenLockEnabled': True,
            }
        
        print(f"✓ {bot_id}")
        print(f"  Daily Loss Limit: ${DAILY_LOSS_LIMIT}")
        print(f"  Profit Lock: ${PROFIT_LOCK}")
        print(f"  Lock When Profit: ${PROFIT_LOCK_ACTIVATION}")
        print(f"  Drawdown Pause: {DRAWDOWN_PAUSE_PERCENT}%")
        print(f"  Pause Duration: {DRAWDOWN_PAUSE_HOURS} hours")
        print()
    
    # Save
    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"{'=' * 60}")
    print(f"✅ BINANCE SAFETY LIMITS ADDED")
    print(f"{'=' * 60}\n")
    print(f"Now bots will:")
    print(f"  • STOP trading when daily loss exceeds ${DAILY_LOSS_LIMIT}")
    print(f"  • LOCK PROFITS at ${PROFIT_LOCK} (when profit reaches ${PROFIT_LOCK_ACTIVATION})")
    print(f"  • PAUSE if drawdown exceeds {DRAWDOWN_PAUSE_PERCENT}%")
    print(f"  • RESUME after {DRAWDOWN_PAUSE_HOURS} hours of cool-down")
    print(f"\n✅ Your $58 Binance account is now PROTECTED\n")

if __name__ == '__main__':
    try:
        add_binance_safety_limits()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
