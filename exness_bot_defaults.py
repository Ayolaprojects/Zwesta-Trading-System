"""
EXNESS BOT DEFAULTS - Permanent Configuration for All New Bots
This file defines the default runtime_state for all newly created Exness bots.
These defaults ensure all bots start with the fixed configuration.

Import this in bot creation scripts and backend to ensure consistency.
"""
from datetime import datetime
import json

# ============================================================================
# EXNESS DEFAULT CONFIGURATION - APPLIES TO ALL NEW EXNESS BOTS
# ============================================================================

EXNESS_BOT_DEFAULTS = {
    # ========================================================================
    # SIGNAL & ENTRY THRESHOLD
    # ========================================================================
    'signalThreshold': 75,  # High confidence: require 75/100 signal quality
    'effectiveSignalThreshold': 75,
    'signalThresholdMode': 'manual',
    'autoSwitch': False,
    'autoAdaptationEnabled': False,
    'allowAdaptiveRawFallback': False,
    'intelligentScanner': False,
    'adaptiveSignalThresholdOffset': 0,
    'adaptiveSignalMissCount': 0,
    'adaptiveSignalThresholdReason': None,
    
    # ========================================================================
    # POSITION SIZING - CONSERVATIVE
    # ========================================================================
    'tradeAmount': 0.5,  # Base: 0.5 lots (conservative)
    'maxLotSize': 0.1,   # Cap: 0.1 lots per position (prevent large losses)
    'scalingMode': 'none',  # No aggressive scaling
    'scalingFactor': 1.0,
    'scalingLimit': 1,
    'effectiveTradeAmount': 0.5,
    'effectivePositionSizeMultiplier': 0.27,
    
    # ========================================================================
    # RISK MANAGEMENT - HARD STOPS
    # ========================================================================
    'maxOpenPositions': 2,  # Max 2 concurrent positions
    'maxPositionsPerSymbol': 1,  # One position per symbol (no pyramiding)
    'maxConsecutiveLosingTrades': 3,  # Pause after 3 losses
    'dailyLossLimit': 50.0,  # Stop at 5% account loss
    'maxDrawdownPercent': 10.0,  # Stop at 10% drawdown
    'maxDailyLoss': 50.0,
    'hardStopLossPercentPerTrade': 2.0,  # 2% per trade max loss
    
    # ========================================================================
    # TAKE PROFIT / STOP LOSS - REALISTIC RATIOS
    # ========================================================================
    'takeProfitPercentage': 2.5,   # TP: 2.5%
    'stopLossPercentage': 1.0,     # SL: 1.0%
    'profitTargetType': 'percentage',
    'stopLossType': 'percentage',
    'minRiskRewardRatio': 2.5,  # Min 2.5:1 ratio
    
    # ========================================================================
    # PYRAMIDING & MARTINGALE - DISABLED
    # ========================================================================
    'pyramidingEnabled': False,
    'pyramidingMaxLayers': 0,
    'pyramidingMultiplier': 1.0,
    'pyramidingDistancePercent': 0,
    'scalingMode': 'none',  # No martingale
    'martingaleEnabled': False,
    'martingaleMultiplier': 1.0,
    
    # ========================================================================
    # TRADE MANAGEMENT - PROTECTIVE
    # ========================================================================
    'postCloseCooldownMinutes': 120,  # 2-hour cooldown after close
    'symbol_cooldown_until': {},  # Clear stale cooldowns
    'maxTradesPerHour': 10,  # Rate limiting
    'minTimeBetweenTradesSeconds': 60,
    'breakEvenEnabled': True,  # Move SL to breakeven after profit
    'breakEvenTriggerProfit': 0.5,
    'trailingStopEnabled': False,  # Don't use trailing stops
    
    # ========================================================================
    # STATE & MANAGEMENT
    # ========================================================================
    'managementState': 'normal',
    'managementProfile': 'balanced',  # Safe default profile
    'consecutiveLosses': 0,
    'lossStreakPauseUntil': None,
    'pauseReason': None,
    'drawdownPauseUntil': None,
    'drawdownPauseSetAt': None,
    'dailyLossTracker': {},
    
    # ========================================================================
    # SYMBOL CONFIGURATION - PROBLEM SYMBOLS DISABLED
    # ========================================================================
    'symbol_config': {
        # Problem symbols (0% win rate - consistent losers)
        'USTECm': {'enabled': False, 'reason': '0% win rate, persistent losses', 'maxLots': 0},
        'AUDUSDm': {'enabled': False, 'reason': '41.8% win rate, avg loss 3.6x win', 'maxLots': 0},
        'ETHUSDm': {'enabled': False, 'reason': '13% win rate, lowest performer', 'maxLots': 0},
        
        # Acceptable symbols (use carefully, still losing)
        'GBPUSDm': {'enabled': False, 'reason': '34% win rate', 'maxLots': 0},
        'XAUUSDm': {'enabled': False, 'reason': '42% win rate', 'maxLots': 0},
        'USDJPYm': {'enabled': True, 'reason': 'Test symbol only', 'maxLots': 0.02},
    },
    
    # ========================================================================
    # ADAPTATION & AUTO-SWITCHING - DISABLED
    # ========================================================================
    'adaptiveMode': False,
    'autoAdaptiveRules': [],
    'allowDynamicAdjustment': False,
    'enableSmartSignalFiltering': False,
    'enableContextualAnalysis': False,
    
    # ========================================================================
    # METADATA
    # ========================================================================
    'bot_defaults_version': '2.0_permanent_fix',
    'defaults_applied_timestamp': datetime.now().isoformat(),
    'defaults_note': 'Permanent fix for Exness bots - all symbols were losing money',
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_exness_defaults():
    """Get a fresh copy of Exness bot defaults (safe for modification)"""
    return json.loads(json.dumps(EXNESS_BOT_DEFAULTS))

def get_defaults_for_broker(broker_name):
    """Get defaults for any broker (extensible for future brokers)"""
    if broker_name.lower() in ('exness', 'mt5'):
        return get_exness_defaults()
    # Add other brokers here
    return {}

def apply_defaults_to_runtime_state(runtime_state, broker_name, preserve_keys=None):
    """
    Merge defaults into existing runtime_state while preserving specified keys.
    
    Args:
        runtime_state (dict): Current runtime state
        broker_name (str): Broker name
        preserve_keys (list): Keys to preserve from runtime_state (don't override)
    
    Returns:
        dict: Updated runtime state with defaults applied
    """
    defaults = get_defaults_for_broker(broker_name)
    preserve_keys = preserve_keys or ['botId', 'bot_id', 'credentialId', 'brokerAccountId', 'symbols', 'created_at']
    
    # Start with defaults
    result = defaults.copy()
    
    # Preserve specified keys from original runtime_state
    if runtime_state:
        for key in preserve_keys:
            if key in runtime_state:
                result[key] = runtime_state[key]
    
    return result

# ============================================================================
# DATABASE UPDATE FUNCTION
# ============================================================================

def update_bot_to_defaults(bot_id, conn=None):
    """
    Update a specific bot to use the new defaults.
    
    Args:
        bot_id (str): Bot ID to update
        conn: SQLite connection (optional, will create if not provided)
    
    Returns:
        bool: Success status
    """
    import sqlite3
    
    should_close = False
    if conn is None:
        conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
        should_close = True
    
    try:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Get current bot config
        cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (bot_id,))
        row = cur.fetchone()
        
        if not row:
            return False
        
        # Apply defaults
        current_state = json.loads(row[0] or '{}') if row[0] else {}
        broker_name = current_state.get('broker', 'Exness')
        
        updated_state = apply_defaults_to_runtime_state(current_state, broker_name)
        updated_state['defaults_applied_at'] = datetime.now().isoformat()
        
        # Update database
        cur.execute(
            "UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?",
            (json.dumps(updated_state), bot_id)
        )
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error updating bot {bot_id}: {e}")
        return False
    finally:
        if should_close:
            conn.close()

# ============================================================================
# EXPORT FOR USE IN BOT CREATION
# ============================================================================

def create_new_bot_runtime_state(
    bot_id,
    user_id,
    broker_account_id,
    credential_id,
    symbols,
    broker='Exness',
    **overrides
):
    """
    Create a complete runtime_state for a new bot with defaults applied.
    
    Args:
        bot_id (str): Bot ID
        user_id (str): User ID
        broker_account_id (str): Broker account ID
        credential_id (str): Credential ID
        symbols (list): Trading symbols
        broker (str): Broker name
        **overrides: Any config values to override defaults
    
    Returns:
        dict: Complete runtime_state ready for database insert
    """
    # Start with defaults
    state = get_defaults_for_broker(broker)
    
    # Add bot-specific data
    state.update({
        'botId': bot_id,
        'bot_id': bot_id,
        'userId': user_id,
        'user_id': user_id,
        'brokerAccountId': broker_account_id,
        'broker_account_id': broker_account_id,
        'credentialId': credential_id,
        'credential_id': credential_id,
        'symbols': symbols,
        'broker': broker,
        'created_at': datetime.now().isoformat(),
        'lastOptimizationTime': datetime.now().isoformat(),
        'optimizationNote': 'Bot created with permanent fix defaults',
    })
    
    # Apply any overrides
    state.update(overrides)
    
    return state

# ============================================================================
# TEST & VALIDATION
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("EXNESS BOT DEFAULTS - VALIDATION TEST")
    print("=" * 80)
    
    # Test 1: Get defaults
    defaults = get_exness_defaults()
    print(f"\n✓ Loaded {len(defaults)} default parameters")
    print(f"  Signal Threshold: {defaults['signalThreshold']}")
    print(f"  Max Position Size: {defaults['maxLotSize']} lots")
    print(f"  TP/SL Ratio: {defaults['takeProfitPercentage']}/{defaults['stopLossPercentage']} = {defaults['takeProfitPercentage']/defaults['stopLossPercentage']:.1f}:1")
    print(f"  Disabled Symbols: {len([s for s in defaults['symbol_config'] if not defaults['symbol_config'][s].get('enabled')])}")
    
    # Test 2: Create new bot state
    new_bot = create_new_bot_runtime_state(
        bot_id='bot_test_123',
        user_id='user_test',
        broker_account_id='Exness_123456',
        credential_id='cred_123',
        symbols=['USDJPYm'],
    )
    print(f"\n✓ Created new bot runtime state with {len(new_bot)} parameters")
    print(f"  Bot ID: {new_bot['bot_id']}")
    print(f"  Symbols: {new_bot['symbols']}")
    
    print("\n✅ All defaults loaded successfully")
