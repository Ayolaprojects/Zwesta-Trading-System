#!/usr/bin/env python3
"""
FIX 2: Increase signal thresholds to 65-75
Problem: Current bots use thresholds of 40-55, which is too permissive
This allows weak-quality signals on alt symbols like ETHUSDT, SOLUSDT
Result: Low win rates (0-20%) on demoted symbols

Solution: Increase to 65-75 range (Exness recommended: 65-70)
This will:
- Reduce entries on weak signals
- Eliminate trades from low-quality setups
- Improve overall win rate and P/L
"""

import sqlite3
import json
import sys

MIN_SIGNAL_THRESHOLD = 68

def fix_signal_thresholds():
    """Increase signal thresholds on all active bots"""
    db = sqlite3.connect('zwesta_trading.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # Get Binance bots (they need higher thresholds)
    cursor.execute("""
        SELECT bot_id, runtime_state 
        FROM user_bots 
        WHERE enabled = 1 AND broker_account_id LIKE '%Binance%'
    """)
    
    bots = cursor.fetchall()
    
    print(f"Found {len(bots)} active Binance bots")
    print(f"Increasing signal threshold to {MIN_SIGNAL_THRESHOLD}+\n")
    
    fixed_count = 0
    
    for bot in bots:
        bot_id = bot['bot_id']
        
        try:
            runtime_state = json.loads(bot['runtime_state'] or '{}')
        except:
            runtime_state = {}
        
        # Update signal threshold in runtime state
        old_threshold = runtime_state.get('signalThreshold', 0)
        if old_threshold < MIN_SIGNAL_THRESHOLD:
            runtime_state['signalThreshold'] = MIN_SIGNAL_THRESHOLD
            runtime_state['signalThresholdUpdated'] = True
            
            # Write back to database
            cursor.execute("""
                UPDATE user_bots 
                SET runtime_state = ? 
                WHERE bot_id = ?
            """, (json.dumps(runtime_state), bot_id))
            
            print(f"[UPDATED] {bot_id}")
            print(f"  Signal Threshold: {old_threshold} -> {MIN_SIGNAL_THRESHOLD}")
            
            fixed_count += 1
    
    db.commit()
    db.close()
    
    print(f"\n✓ Updated {fixed_count} bots with higher signal thresholds\n")
    return fixed_count > 0

if __name__ == '__main__':
    if fix_signal_thresholds():
        print("IMPORTANT: Restart backend or clear signal cache for changes to take effect")
    else:
        print("No updates needed")
