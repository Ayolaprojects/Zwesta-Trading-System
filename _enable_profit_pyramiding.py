"""
Profit Pyramiding System - Scale Into Winners
When trade crosses into profit, increase position size to maximize gains
Target: R5 → R50+ profits, Binance 5%+ daily
"""

import sys
import os
sys.path.insert(0, r'c:\zwesta-trader\Zwesta Flutter App')

import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\backend\zwesta_trading.db'

def enable_profit_pyramiding():
    """
    Enable aggressive profit pyramiding:
    - When trade goes +0.5%, add 2x position
    - When trade goes +1.0%, add 3x position  
    - When trade goes +2.0%, add 5x position
    - Target: Turn R5 into R50+ per trade
    """
    
    print("""
╔════════════════════════════════════════════════════════════╗
║   Profit Pyramiding System Activation                     ║
║   Scale Into Winners - Maximize Profitable Trades         ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all active bots
    cursor.execute('''
        SELECT bot_id, user_id, broker_type, is_live, runtime_state, enabled
        FROM user_bots
        WHERE enabled = 1
        ORDER BY broker_type, is_live DESC
    ''')
    
    bots = cursor.fetchall()
    
    print(f"\n📊 Found {len(bots)} active bots\n")
    
    updated_count = 0
    
    for bot in bots:
        bot_id = bot['bot_id']
        broker = bot['broker_type']
        is_live = bot['is_live']
        
        try:
            runtime_state = json.loads(bot['runtime_state']) if bot['runtime_state'] else {}
        except:
            runtime_state = {}
        
        print(f"🤖 {bot_id} ({broker} {'LIVE' if is_live else 'Demo'})")
        
        # Enhanced pyramiding configuration
        profit_pyramiding_config = {
            "enabled": True,
            "strategy": "aggressive_scaling",
            
            # Profit thresholds and multipliers
            "pyramid_levels": [
                {
                    "profit_threshold_pct": 0.3,   # +0.3% profit
                    "size_multiplier": 1.5,         # Increase position by 50%
                    "description": "Small profit confirmed"
                },
                {
                    "profit_threshold_pct": 0.5,   # +0.5% profit
                    "size_multiplier": 2.0,         # Double the position
                    "description": "Good profit momentum"
                },
                {
                    "profit_threshold_pct": 1.0,   # +1.0% profit
                    "size_multiplier": 3.0,         # Triple the position
                    "description": "Strong trend confirmed"
                },
                {
                    "profit_threshold_pct": 1.5,   # +1.5% profit
                    "size_multiplier": 4.0,         # 4x position
                    "description": "Excellent momentum"
                },
                {
                    "profit_threshold_pct": 2.0,   # +2.0% profit
                    "size_multiplier": 5.0,         # 5x position
                    "description": "Maximum scaling"
                }
            ],
            
            # Risk management for pyramiding
            "max_total_multiplier": 10.0,  # Never exceed 10x initial position
            "partial_close_on_reversal": True,  # Close added positions if price reverses
            "reversal_threshold_pct": -0.2,  # Close pyramids if drops 0.2% from peak
            "lock_profit_at_pct": 2.5,  # Move SL to breakeven when +2.5%
            
            # Binance-specific aggressive settings
            "binance_daily_target_pct": 5.0,  # 5% daily minimum target
            "binance_max_leverage": 10,  # Use up to 10x leverage on Binance Futures
            "binance_compound_wins": True,  # Reinvest profits immediately
            
            # Exness-specific settings  
            "exness_profit_multiplier": 10.0,  # Turn R5 into R50
            "exness_base_lot_increase": 0.02,  # Add 0.02 lots per pyramid level
            "exness_max_lot_per_trade": 1.0,   # Max 1.0 lot total per trade
            
            # Exit strategy
            "take_profit_levels": [
                {"pct": 2.0, "close_pct": 25},   # Close 25% at +2%
                {"pct": 3.0, "close_pct": 25},   # Close 25% at +3%
                {"pct": 5.0, "close_pct": 50},   # Close 50% at +5%
                # Let remaining ride with trailing SL
            ],
            
            "trailing_stop_activation_pct": 1.5,  # Activate trailing SL at +1.5%
            "trailing_stop_distance_pct": 0.5,    # Trail by 0.5%
        }
        
        # Update runtime state
        runtime_state['profit_pyramiding'] = profit_pyramiding_config
        
        # Increase base multipliers for more aggressive sizing
        if broker == 'Binance':
            runtime_state['base_multiplier'] = 1.2  # Start 20% larger
            runtime_state['recovery_multiplier'] = 0.85  # Faster recovery
            runtime_state['min_multiplier'] = 0.70  # Higher floor
            print("   💰 Binance: 5% daily target, 10x leverage, aggressive pyramiding")
            
        elif broker == 'Exness':
            runtime_state['base_multiplier'] = 1.0
            runtime_state['profit_target_multiplier'] = 10.0  # 10x profit target
            runtime_state['min_lot_size'] = 0.05  # Larger minimum
            runtime_state['max_lot_size'] = 1.0   # Allow up to 1.0 lot
            print("   💎 Exness: 10x profit scaling (R5 → R50)")
        
        # Update database
        cursor.execute('''
            UPDATE user_bots
            SET runtime_state = ?
            WHERE bot_id = ?
        ''', (json.dumps(runtime_state), bot_id))
        
        updated_count += 1
        print("   ✅ Profit pyramiding enabled\n")
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print(f"✅ Updated {updated_count} bots with profit pyramiding")
    print("=" * 60)
    
    print("""
🎯 PROFIT TARGETS ACTIVATED:

📈 Pyramiding Levels:
   +0.3% profit → 1.5x position size
   +0.5% profit → 2.0x position size
   +1.0% profit → 3.0x position size
   +1.5% profit → 4.0x position size
   +2.0% profit → 5.0x position size

💰 Profit Targets:
   Exness: R5 → R50+ per trade (10x scaling)
   Binance: 5% daily minimum (compound wins)

🛡️ Risk Management:
   Max total position: 10x initial
   Trailing stop: Activated at +1.5%
   Partial exits: 25% @ +2%, 25% @ +3%, 50% @ +5%
   Reversal protection: Close pyramids if -0.2% from peak

⚡ Binance Futures:
   Leverage: Up to 10x
   Daily target: 5% minimum
   Auto-compound: Reinvest all wins

💎 Exness Forex:
   Base lot increase: 0.02 per level
   Max lot per trade: 1.0
   Target: 10x current profits

🚨 IMPORTANT:
   - Restart backend to apply changes
   - Monitor first few trades closely
   - Ensure sufficient margin (10x position needs 10x margin)
   - Works best in trending markets
   - Will close pyramids on reversals to protect profits

📊 Expected Performance:
   Current: R0.49 - R7.05 per trade
   Target:  R5.00 - R70.00 per trade (10x average)
   Binance: 5% account growth per day = 150%/month

⚠️  This is AGGRESSIVE - ensure you have:
   1. Sufficient account balance (recommend R10k+ per bot)
   2. Good risk tolerance (drawdowns can be 20-30%)
   3. Trending market conditions (pyramiding fails in choppy markets)
    """)
    
    return updated_count

if __name__ == '__main__':
    try:
        count = enable_profit_pyramiding()
        
        print(f"\n{'='*60}")
        print("🎯 Next Steps:")
        print("="*60)
        print("1. Restart backend:")
        print("   cd C:\\backend")
        print("   python multi_broker_backend_updated.py")
        print()
        print("2. Monitor first trades in admin dashboard")
        print()
        print("3. Check profit scaling is working:")
        print("   - Trades should increase in size as they profit")
        print("   - Look for 2x, 3x, 5x position additions")
        print()
        print("4. Verify account has sufficient margin for 10x positions")
        print()
        print("🚀 Ready to scale R5 trades into R50+ winners!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
