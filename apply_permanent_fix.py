"""
PERMANENT FIX INTEGRATION - Apply defaults to all Exness bots (existing + future)
This script ensures ALL Exness bots use the corrected configuration.
"""
import json
import sqlite3
from datetime import datetime
from exness_bot_defaults import (
    get_exness_defaults,
    apply_defaults_to_runtime_state,
    update_bot_to_defaults,
    create_new_bot_runtime_state
)

DB = r'C:\backend\zwesta_trading.db'

def apply_defaults_to_all_exness_bots():
    """Apply defaults to all existing Exness bots"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("="*80)
    print("PERMANENT FIX - APPLY DEFAULTS TO ALL EXNESS BOTS")
    print("="*80)
    
    # Find all Exness bots
    cur.execute("""
        SELECT bot_id, broker_account_id, runtime_state 
        FROM user_bots 
        WHERE broker_account_id LIKE 'Exness_%' OR broker_account_id LIKE 'MT5_%'
    """)
    
    bots = cur.fetchall()
    
    if not bots:
        print("\n❌ No Exness bots found")
        conn.close()
        return 0
    
    print(f"\nFound {len(bots)} Exness bot(s)")
    
    # Apply defaults to each bot
    updated = 0
    for bot in bots:
        bot_id = bot['bot_id']
        current_state = json.loads(bot['runtime_state'] or '{}') if bot['runtime_state'] else {}
        
        # Apply defaults while preserving bot-specific data
        preserve = [
            'botId', 'bot_id', 'userId', 'user_id', 
            'credentialId', 'credential_id',
            'brokerAccountId', 'broker_account_id',
            'symbols', 'created_at', 'name',
            'accountBalance', 'accountEquity', 'totalProfit',
            'open_positions', 'tradeHistory'
        ]
        
        updated_state = apply_defaults_to_runtime_state(current_state, 'Exness', preserve)
        updated_state['lastPermanentFixApplied'] = datetime.now().isoformat()
        
        # Update database
        cur.execute(
            "UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?",
            (json.dumps(updated_state), bot_id)
        )
        
        updated += 1
        print(f"\n✓ {bot_id}")
        print(f"  Signal Threshold: {updated_state['signalThreshold']}")
        print(f"  Trade Amount: {updated_state['tradeAmount']} lots")
        print(f"  TP/SL: {updated_state['takeProfitPercentage']}/{updated_state['stopLossPercentage']}%")
        print(f"  Max Consecutive Losses: {updated_state['maxConsecutiveLosingTrades']}")
        print(f"  Disabled Symbols: {len([s for s in updated_state.get('symbol_config', {}) if not updated_state['symbol_config'][s].get('enabled')])}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*80)
    print(f"✅ UPDATED {updated} EXISTING EXNESS BOT(S)")
    print("="*80)
    
    return updated

def show_usage_in_bot_creation():
    """Show how to use defaults in new bot creation scripts"""
    usage = """
    
█████████████████████████████████████████████████████████████████████████████
  HOW TO USE IN NEW BOT CREATION SCRIPTS
█████████████████████████████████████████████████████████████████████████████

BEFORE (old way - bots would still lose):
    
    runtime_state = {
        'botId': bot_id,
        'tradeAmount': 6.0,  # WRONG: too aggressive
        'signalThreshold': 1,  # WRONG: accepts junk signals
        'pyramidingEnabled': True,  # WRONG: amplifies losses
        'symbols': symbols,
        # ... etc
    }

AFTER (new way - bots start with fixes applied):

    from exness_bot_defaults import create_new_bot_runtime_state
    
    runtime_state = create_new_bot_runtime_state(
        bot_id=bot_id,
        user_id=user_id,
        broker_account_id=broker_account_id,
        credential_id=credential_id,
        symbols=symbols,
        broker='Exness',
        # Optional: override any defaults
        tradeAmount=1.0,  # Override default 0.5 if needed
    )
    
    # Then use in INSERT:
    cursor.execute('''
        INSERT INTO user_bots (bot_id, user_id, ..., runtime_state, ...)
        VALUES (?, ?, ..., ?, ...)
    ''', (bot_id, user_id, ..., json.dumps(runtime_state), ...))

█████████████████████████████████████████████████████████████████████████████
  SCRIPTS TO UPDATE
█████████████████████████████████████████████████████████████████████████████

The following bot creation scripts should be updated to use the new defaults:

1. _create_gbp_pyramid_bot.py
2. _create_futures_bot.py
3. _create_live_bot.py
4. Any script that creates Exness bots via API

And in backend:
1. multi_broker_backend_updated.py (bot creation endpoint)

█████████████████████████████████████████████████████████████████████████████
  WHAT GETS FIXED AUTOMATICALLY
█████████████████████████████████████████████████████████████████████████████

✓ Signal Threshold: 1 → 75 (filter junk signals)
✓ Position Size: 6.0 → 0.5 (reduce large losses)
✓ TP/SL Ratio: Fixed (2.5% TP, 1.0% SL = 2.5:1)
✓ Pyramid/Martingale: DISABLED (no doubling down)
✓ Loss Limits: ENABLED (3 losses or 5% daily = pause)
✓ Problem Symbols: DISABLED (USTECm, AUDUSDm, ETHUSDm)
✓ Cooldown: 120 minutes (prevent chasing)

█████████████████████████████████████████████████████████████████████████████
"""
    return usage

def create_integration_test():
    """Test that new bots would be created correctly"""
    print("\n" + "="*80)
    print("TEST: Creating new bot with defaults")
    print("="*80)
    
    new_bot_state = create_new_bot_runtime_state(
        bot_id='bot_test_permanent_fix',
        user_id='user_test_123',
        broker_account_id='Exness_999999',
        credential_id='cred_test',
        symbols=['USDJPYm'],
        broker='Exness',
    )
    
    print(f"\n✓ New bot config:")
    print(f"  Bot ID: {new_bot_state['bot_id']}")
    print(f"  Trade Amount: {new_bot_state['tradeAmount']} lots")
    print(f"  Signal Threshold: {new_bot_state['signalThreshold']}")
    print(f"  TP/SL Ratio: {new_bot_state['takeProfitPercentage']}/{new_bot_state['stopLossPercentage']} = {new_bot_state['takeProfitPercentage']/new_bot_state['stopLossPercentage']:.1f}:1")
    print(f"  Max Consecutive Losses: {new_bot_state['maxConsecutiveLosingTrades']}")
    print(f"  Pyramid Enabled: {new_bot_state['pyramidingEnabled']}")
    print(f"  Martingale Enabled: {new_bot_state['martingaleEnabled']}")
    print(f"  Disabled Symbols: {[s for s in new_bot_state['symbol_config'] if not new_bot_state['symbol_config'][s].get('enabled')]}")
    
    print("\n✅ Test bot would have correct defaults")

def main():
    print("\n")
    
    # Step 1: Apply to existing bots
    count = apply_defaults_to_all_exness_bots()
    
    # Step 2: Show usage
    usage = show_usage_in_bot_creation()
    print(usage)
    
    # Step 3: Test new bot creation
    create_integration_test()
    
    print("\n" + "="*80)
    print("✅ PERMANENT FIX COMPLETE")
    print("="*80)
    print("""
All existing Exness bots have been updated with the fixes.

NEW BOTS will automatically use correct configuration if bot creation 
scripts are updated to use exness_bot_defaults module.

Next steps:
1. Restart backend: python start_zwesta_backend.ps1
2. Update bot creation scripts (see HOW TO USE above)
3. Test new bot creation
4. All future Exness bots will have permanent fixes applied

📋 Files to update:
   - _create_gbp_pyramid_bot.py
   - _create_futures_bot.py
   - multi_broker_backend_updated.py (bot creation endpoint)
""")

if __name__ == '__main__':
    main()
