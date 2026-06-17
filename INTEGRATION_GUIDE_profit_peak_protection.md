"""
INTEGRATION GUIDE: Profit Peak Erosion Protection in multi_broker_backend_updated.py

This guide shows exactly where and how to integrate the profit peak protection system
to prevent ETH/SOL/BTC from eroding profits after reaching a peak.

CHANGES NEEDED:
1. Import the profit peak protection module
2. Record trades AFTER they close (in the trade closing section)
3. Check cooldown/recovery status BEFORE selecting symbols (in symbol iteration)
4. Reduce position size for symbols in recovery mode (in place_trade)

LINE NUMBERS (approximate - search for key text):
- L~39900: continuous_bot_trading_loop() starts
- L~39700-39750: Symbol iteration loop "for symbol in symbols:"
- L~10520: Trade closing section (after order closes)
- L~15341: place_trade() function

STEP 1: ADD IMPORT AT TOP
=========================================================================
Near line ~1 of multi_broker_backend_updated.py, add:

    from fix_profit_peak_erosion import (
        record_symbol_trade,
        should_trade_symbol_with_peak_protection,
        calculate_recovery_position_size,
        format_symbol_protection_summary,
    )

STEP 2: RECORD TRADE COMPLETION
=========================================================================
When a trade closes (after position closes), record the P/L:

Location: Around line ~10520 where trades are closed

Current code pattern:
    if matched_pos:
        trade_profit = matched_pos.get('profit') or matched_pos.get('pnl') or 0
        # Trade closing logic...

ADD AFTER trade closes successfully:
    ────────────────────────────────────────────────────────────────
    # Record trade for profit peak protection
    try:
        bot_config = record_symbol_trade(
            bot_config,
            symbol=symbol,
            trade_profit=float(trade_profit or 0),
            keep_history=10
        )
        
        # Log if profit peak detected
        peak_data = bot_config.get('symbolPeakDetection', {}).get(symbol, {})
        if peak_data.get('peak_detected'):
            logger.warning(
                f"⚠️ Bot {bot_id}: PROFIT PEAK DETECTED on {symbol}! "
                f"Peak: ${peak_data.get('peak_cumulative_profit', 0):.2f}, "
                f"Declined: ${peak_data.get('decline_magnitude', 0):.2f} "
                f"→ Activating 15-minute cooldown"
            )
    except Exception as peak_record_error:
        logger.debug(f"Bot {bot_id}: Could not record peak protection: {peak_record_error}")
    ────────────────────────────────────────────────────────────────

STEP 3: CHECK PEAK PROTECTION BEFORE TRADING
=========================================================================
In the symbol iteration loop where we decide whether to trade each symbol:

Location: Around line ~39950 inside "for symbol in symbols:"

Current code:
    for symbol in symbols:
        if bot_stop_flags.get(bot_id, False):
            break
        
        # Market hours check...
        symbol_is_open, symbol_market_status = ...
        if not symbol_is_open:
            logger.info(f"⏭️ Bot {bot_id}: Skipping {symbol} - {symbol_market_status}")
            continue

ADD AFTER market check:
    ────────────────────────────────────────────────────────────────
        # Check profit peak protection before trading
        should_trade, peak_reason = should_trade_symbol_with_peak_protection(
            bot_config,
            symbol,
        )
        if not should_trade:
            logger.info(f"⏭️ Bot {bot_id}: {peak_reason} - skipping this cycle")
            last_order_block_reason = peak_reason
            continue
    ────────────────────────────────────────────────────────────────

STEP 4: ADJUST POSITION SIZE FOR RECOVERY MODE
=========================================================================
When calculating position size for a trade (in continuous_bot_trading_loop):

Location: Around line ~40200-40300 where trade parameters are set

Current code:
    trade_params = {
        'symbol': symbol,
        'volume': calculate_position_size(bot_config, ...),
        ...
    }

MODIFY to:
    ────────────────────────────────────────────────────────────────
    base_volume = calculate_position_size(bot_config, ...)
    
    # Apply recovery mode position size reduction
    recovery_mode = bot_config.get('symbolRecoveryMode', {}).get(symbol, {})
    if recovery_mode.get('active'):
        recovery_wins = recovery_mode.get('consecutive_wins', 0)
        adjusted_volume = calculate_recovery_position_size(
            base_volume,
            recovery_mode_active=True,
            recovery_win_count=recovery_wins,
        )
        if adjusted_volume < base_volume:
            logger.info(
                f"📉 Bot {bot_id}: Reduced {symbol} position size from "
                f"{base_volume} to {adjusted_volume} (recovery mode: {recovery_wins}/3 wins)"
            )
            base_volume = adjusted_volume
    
    trade_params = {
        'symbol': symbol,
        'volume': base_volume,
        ...
    }
    ────────────────────────────────────────────────────────────────

STEP 5: LOG PROTECTION STATUS PERIODICALLY
=========================================================================
Add to the main bot loop status logging (around line ~40300):

    ────────────────────────────────────────────────────────────────
    # Log profit protection status every 10 cycles
    if trade_cycle % 10 == 0:
        try:
            protection_status = format_symbol_protection_summary(bot_config)
            logger.info(protection_status)
        except Exception as e:
            logger.debug(f"Bot {bot_id}: Could not format protection status: {e}")
    ────────────────────────────────────────────────────────────────

EXPECTED BEHAVIOR AFTER INTEGRATION
=========================================================================

BEFORE (Current problematic behavior):
  Trade 1: ETH +$0.45
  Trade 2: ETH +$0.50
  Trade 3: ETH +$0.26  ← Profit peak $1.21
  Trade 4: ETH -$0.15  ← No protection, bot keeps trading
  Trade 5: ETH -$0.08  ← Profit eroding
  Trade 6: ETH -$0.12  ← Losses accumulate
  Total: -$0.85

AFTER (With profit peak protection):
  Trade 1: ETH +$0.45
  Trade 2: ETH +$0.50
  Trade 3: ETH +$0.26  ← Profit peak $1.21 detected!
  Trade 4: ETH -$0.15  ← Triggers protection, cooldown activated
  Trade 5: USDT +$0.42 ← Bot rotates to other symbol (SOL, BTC, USD)
  Trade 6: SOL +$0.38  ← Diversified, ETH has 15-minute cooldown
  Trade 7: ETH +$0.35  ← After cooldown, recovers profit
  Total: +$2.71       ← No erosion, better diversification

COOLDOWN MECHANICS
=========================================================================
- Duration: 15 minutes (configurable)
- Triggers: When peak profit erodes by $0.05+ after reaching $0.50+
- Effect: Symbol skipped for 2-3 trading cycles
- Alternative: Other symbols trade instead (BTC, SOL, USDT, etc.)

RECOVERY MODE MECHANICS
=========================================================================
- Activation: Same time as cooldown
- Position size: Reduced to 50% of normal
- Exit condition: 3 consecutive winning trades
- Re-entry: Back to full position size after graduation
- Purpose: Prove profitability before risking full position again

BENEFITS
=========================================================================
✅ Prevents profit erosion on peak-hit symbols
✅ Forces healthier symbol rotation
✅ Maintains profit lock protection for ETH/SOL/BTC
✅ Reduces false entries on declining momentum
✅ Speeds recovery through position size management
✅ Logs exactly which symbols are protected/why

TESTING BEFORE DEPLOYMENT
=========================================================================
1. Run bot with new symbols that typically lose (ETH, SOL)
2. Watch logs for "PEAK DETECTED" messages
3. Verify cooldown prevents re-entry
4. Check position sizing reduction
5. Verify recovery mode graduation after 3 wins
6. Test with 1 bot first, then scale to fleet

POTENTIAL ISSUES & FIXES
=========================================================================
Issue: Symbol never trades again after peak
  → Check cooldown expiration (15 minutes)
  → Verify recovery mode graduated (3 wins needed)

Issue: Position sizes too small in recovery
  → Adjust recovery_multiplier (currently 0.50)
  → Change in calculate_recovery_position_size()

Issue: Peaks detected too frequently
  → Increase min_peak_profit parameter (currently $0.50)
  → Increase decline threshold (currently $0.05)

Issue: Cooldown too long, missing recoveries
  → Reduce cooldown_minutes (currently 15)
  → Set to 5-10 minutes for faster rotation
"""

# Quick reference: Key functions to call

def example_usage():
    """Example showing how to use the module"""
    
    from fix_profit_peak_erosion import (
        record_symbol_trade,
        should_trade_symbol_with_peak_protection,
        calculate_recovery_position_size,
    )
    
    # Initialize bot config with tracking structures
    bot_config = {
        'symbols': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'position_size': 0.10,
    }
    
    # === AFTER EACH TRADE CLOSES ===
    trade_profit = 0.45  # e.g., $0.45 profit
    symbol = 'ETHUSDT'
    
    # Record the trade for peak detection
    bot_config = record_symbol_trade(bot_config, symbol, trade_profit)
    
    # === BEFORE EACH TRADE ===
    # Check if symbol is in cooldown/recovery
    can_trade, reason = should_trade_symbol_with_peak_protection(bot_config, symbol)
    
    if not can_trade:
        print(f"Skip {symbol}: {reason}")
        # Try next symbol...
    else:
        # Calculate position size (may be reduced if in recovery)
        base_size = 0.10
        recovery_active = bot_config.get('symbolRecoveryMode', {}).get(symbol, {}).get('active', False)
        recovery_wins = bot_config.get('symbolRecoveryMode', {}).get(symbol, {}).get('consecutive_wins', 0)
        
        position_size = calculate_recovery_position_size(
            base_size,
            recovery_active,
            recovery_wins
        )
        
        print(f"Trade {symbol} with size {position_size}")


if __name__ == '__main__':
    print(__doc__)
    print("\n" + "="*70)
    print("Example usage:")
    print("="*70)
    example_usage()
