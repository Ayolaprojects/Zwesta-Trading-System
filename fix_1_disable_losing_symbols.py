#!/usr/bin/env python3
"""
URGENT FIX: Disable losing symbols on all bots
These symbols have 0-20% win rates and are consistently losing:
- ETHUSDT: -4.01 USDT (20% win rate)
- SOLUSDT: -3.05 USDT (0% win rate)
- BNBUSDT: -0.24 USDT (33% win rate)
"""

import sqlite3
import json
import sys

LOSING_SYMBOLS = {'ETHUSDT', 'SOLUSDT', 'BNBUSDT'}

def fix_bot_symbols():
    """Remove losing symbols from all bots' symbol lists"""
    db = sqlite3.connect('zwesta_trading.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    cursor.execute("SELECT bot_id, symbols, runtime_state FROM user_bots WHERE enabled = 1")
    bots = cursor.fetchall()
    
    print(f"Found {len(bots)} active bots")
    print(f"Removing symbols: {', '.join(LOSING_SYMBOLS)}\n")
    
    fixed_count = 0
    
    for bot in bots:
        bot_id = bot['bot_id']
        symbols_str = bot['symbols'] or ''
        
        # Parse symbols
        old_symbols = set(s.strip() for s in symbols_str.split(',') if s.strip())
        new_symbols = old_symbols - LOSING_SYMBOLS
        
        if new_symbols != old_symbols:
            new_symbols_str = ','.join(sorted(new_symbols))
            
            # Update database
            cursor.execute("""
                UPDATE user_bots 
                SET symbols = ? 
                WHERE bot_id = ?
            """, (new_symbols_str, bot_id))
            
            print(f"[FIXED] {bot_id}")
            print(f"  Before: {symbols_str}")
            print(f"  After:  {new_symbols_str}")
            
            fixed_count += 1
    
    db.commit()
    db.close()
    
    print(f"\n✓ Fixed {fixed_count} bots\n")
    return fixed_count > 0

if __name__ == '__main__':
    if fix_bot_symbols():
        print("IMPORTANT: Restart the backend for changes to take effect")
        print("  or manually kill/restart affected bots via API")
    else:
        print("No bots needed fixing")
