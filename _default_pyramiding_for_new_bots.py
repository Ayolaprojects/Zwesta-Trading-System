"""
Add this function to multi_broker_backend_updated.py
to ensure ALL new bots get profit pyramiding configuration automatically
"""

def get_default_profit_pyramiding_config(broker_type: str, is_live: bool = False):
    """
    Generate default profit pyramiding configuration for new bots
    This ensures newly created bots automatically have pyramiding enabled
    
    Args:
        broker_type: 'Binance', 'Exness', etc.
        is_live: Whether this is a live or demo bot
    
    Returns:
        Dict with pyramiding configuration
    """
    
    # Base pyramiding configuration (applies to all brokers)
    config = {
        "enabled": True,
        "strategy": "aggressive_scaling",
        
        # Profit thresholds and multipliers
        "pyramid_levels": [
            {
                "profit_threshold_pct": 0.3,
                "size_multiplier": 1.5,
                "description": "Small profit confirmed"
            },
            {
                "profit_threshold_pct": 0.5,
                "size_multiplier": 2.0,
                "description": "Good profit momentum"
            },
            {
                "profit_threshold_pct": 1.0,
                "size_multiplier": 3.0,
                "description": "Strong trend confirmed"
            },
            {
                "profit_threshold_pct": 1.5,
                "size_multiplier": 4.0,
                "description": "Excellent momentum"
            },
            {
                "profit_threshold_pct": 2.0,
                "size_multiplier": 5.0,
                "description": "Maximum scaling"
            }
        ],
        
        # Risk management
        "max_total_multiplier": 10.0,
        "partial_close_on_reversal": True,
        "reversal_threshold_pct": -0.2,
        "lock_profit_at_pct": 2.5,
        
        # Exit strategy
        "take_profit_levels": [
            {"pct": 2.0, "close_pct": 25},
            {"pct": 3.0, "close_pct": 25},
            {"pct": 5.0, "close_pct": 50},
        ],
        
        "trailing_stop_activation_pct": 1.5,
        "trailing_stop_distance_pct": 0.5,
    }
    
    # Broker-specific customizations
    if canonicalize_broker_name(broker_type) == 'Binance':
        config.update({
            "binance_daily_target_pct": 5.0,
            "binance_max_leverage": 10,
            "binance_compound_wins": True,
            "base_multiplier": 1.2,  # Start 20% larger
            "recovery_multiplier": 0.85,
            "min_multiplier": 0.70,
        })
    
    elif canonicalize_broker_name(broker_type) in ['Exness', 'XM', 'XM Global', 'FXCM']:
        config.update({
            "exness_profit_multiplier": 10.0,  # Turn R5 into R50
            "exness_base_lot_increase": 0.02,
            "exness_max_lot_per_trade": 1.0,
            "base_multiplier": 1.0,
            "profit_target_multiplier": 10.0,
            "min_lot_size": 0.05,
            "max_lot_size": 1.0,
        })
    
    # Be more conservative on live accounts (optional - can be adjusted)
    if is_live:
        # Reduce pyramid levels slightly for live
        config["max_total_multiplier"] = 8.0  # 8x instead of 10x
        config["reversal_threshold_pct"] = -0.15  # Tighter stop on reversals
    
    return config


# ==================== INTEGRATION POINT ====================
# Add this to the bot creation flow in create_bot() function
# Around line 33200 where active_bots[bot_id] is populated

"""
In create_bot() function, after setting up the active_bots[bot_id] dictionary,
add this line before persist_bot_runtime_state(bot_id, force=True):

    # Add default profit pyramiding configuration for new bots
    active_bots[bot_id]['profit_pyramiding'] = get_default_profit_pyramiding_config(
        broker_type=broker_name,
        is_live=bool(is_live)
    )

This ensures ALL newly created bots automatically get pyramiding enabled!
"""

# Example of where to add it:
"""
active_bots[bot_id] = {
    'botId': bot_id,
    'user_id': user_id,
    # ... all existing fields ...
    'open_positions': {},
}

# NEW: Add default profit pyramiding for all new bots
active_bots[bot_id]['profit_pyramiding'] = get_default_profit_pyramiding_config(
    broker_type=broker_name,
    is_live=bool(is_live)
)

# Force immediate persistence
persist_bot_runtime_state(bot_id, force=True)
"""
