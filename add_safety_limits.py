#!/usr/bin/env python3
"""
Add daily loss limits and drawdown protection to all Exness bots
"""

import json
import shutil
from datetime import datetime

STATUS_FILE = 'bot_status.json'

# Safe defaults for Exness
DAILY_LOSS_LIMIT = 50.0  # Stop trading after $50 loss
DRAWDOWN_PAUSE_PERCENT = 5.0  # Pause at 5% drawdown
DRAWDOWN_PAUSE_HOURS = 8.0  # Resume after 8 hours

def add_safety_limits():
    """Add daily loss limits to all Exness bots"""
    
    # Backup
    backup = f"{STATUS_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(STATUS_FILE, backup)
    print(f"💾 Backed up to: {backup}\n")
    
    # Load bots
    with open(STATUS_FILE, 'r') as f:
        data = json.load(f)
    
    exness_bots = [b for b in data.get('bots', []) if b.get('broker_type') == 'Exness']
    
    print(f"{'=' * 60}")
    print(f"ADDING DAILY LOSS LIMITS TO EXNESS BOTS")
    print(f"{'=' * 60}\n")
    
    for bot in exness_bots:
        bot_id = bot['botId']
        
        # Set safety limits
        bot['maxDailyLoss'] = DAILY_LOSS_LIMIT
        bot['drawdownPausePercent'] = DRAWDOWN_PAUSE_PERCENT
        bot['drawdownPauseHours'] = DRAWDOWN_PAUSE_HOURS
        
        print(f"✓ {bot_id}")
        print(f"  Daily Loss Limit: ${DAILY_LOSS_LIMIT}")
        print(f"  Drawdown Pause: {DRAWDOWN_PAUSE_PERCENT}%")
        print(f"  Pause Duration: {DRAWDOWN_PAUSE_HOURS} hours")
        print()
    
    # Save
    with open(STATUS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"{'=' * 60}")
    print(f"✅ SAFETY LIMITS ADDED")
    print(f"{'=' * 60}\n")
    print(f"Now bots will STOP trading when:")
    print(f"  • Daily loss exceeds ${DAILY_LOSS_LIMIT}")
    print(f"  • Drawdown exceeds {DRAWDOWN_PAUSE_PERCENT}%")
    print(f"\n⏸️  Pause lasts {DRAWDOWN_PAUSE_HOURS} hours before resuming")
    print(f"\n✅ Your $50 account is now PROTECTED\n")

if __name__ == '__main__':
    try:
        add_safety_limits()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
