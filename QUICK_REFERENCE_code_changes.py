"""
QUICK REFERENCE: Exact Code Changes for Profit Peak Protection

Copy these code blocks directly into multi_broker_backend_updated.py
at the locations specified.

TEST FIRST: Run fix_profit_peak_erosion.py to understand the system before implementing!
"""

# ============================================================================
# CHANGE 1: ADD IMPORT (Line ~1-50, with other imports)
# ============================================================================
CHANGE_1_CODE = """
# Profit peak erosion protection (new feature - line ~40-50)
try:
    from fix_profit_peak_erosion import (
        record_symbol_trade,
        should_trade_symbol_with_peak_protection,
        calculate_recovery_position_size,
        format_symbol_protection_summary,
    )
    PROFIT_PEAK_PROTECTION_AVAILABLE = True
except ImportError:
    PROFIT_PEAK_PROTECTION_AVAILABLE = False
    logger.warning("⚠️ Profit peak erosion protection module not available - feature disabled")
"""

# ============================================================================
# CHANGE 2: ADD CONFIG FLAGS (Line ~400-500, with other configs)
# ============================================================================
CHANGE_2_CODE = """
# Profit peak erosion protection configuration (new - line ~410-420)
PROFIT_PEAK_PROTECTION_ENABLED = True  # Set to False to disable feature
PROFIT_PEAK_PROTECTION_COOLDOWN_MINUTES = 15  # After peak detected, how long to wait
PROFIT_PEAK_PROTECTION_MIN_PEAK_PROFIT = 0.50  # Minimum profit to arm detection ($)
PROFIT_PEAK_PROTECTION_DECLINE_THRESHOLD = 0.05  # Min decline to trigger cooldown ($)
PROFIT_PEAK_PROTECTION_RECOVERY_WINS_REQUIRED = 3  # Wins needed to graduate recovery
PROFIT_PEAK_PROTECTION_RECOVERY_SIZE_PERCENT = 0.50  # Position size % in recovery (50%)
"""

# ============================================================================
# CHANGE 3: RECORD TRADE (Line ~10520, after trade closes)
# ============================================================================
CHANGE_3_CODE = """
# After this block where trade closes:
if matched_pos:
    trade_profit = matched_pos.get('profit') or matched_pos.get('pnl') or 0
    # ... existing trade closing code ...
    trades_placed += 1

# ADD THIS RIGHT AFTER THE BLOCK ABOVE (~line 10530):
                        # Record trade for profit peak protection
                        if PROFIT_PEAK_PROTECTION_AVAILABLE and PROFIT_PEAK_PROTECTION_ENABLED:
                            try:
                                symbol_for_record = str(symbol or matched_pos.get('symbol', ''))
                                trade_profit_for_record = float(trade_profit or 0)
                                
                                bot_config = record_symbol_trade(
                                    bot_config,
                                    symbol=symbol_for_record,
                                    trade_profit=trade_profit_for_record,
                                    keep_history=10
                                )
                                
                                # Log if profit peak detected
                                peak_data = bot_config.get('symbolPeakDetection', {}).get(symbol_for_record, {})
                                if peak_data.get('peak_detected'):
                                    logger.warning(
                                        f"⚠️ Bot {bot_id}: PROFIT PEAK DETECTED on {symbol_for_record}! "
                                        f"Peak: ${peak_data.get('peak_cumulative_profit', 0):.2f}, "
                                        f"Declined: ${peak_data.get('decline_magnitude', 0):.2f} → "
                                        f"Activating {PROFIT_PEAK_PROTECTION_COOLDOWN_MINUTES}-minute cooldown"
                                    )
                                    bot_config['_lastProfitPeakSymbol'] = symbol_for_record
                                    bot_config['_lastProfitPeakTime'] = datetime.now().isoformat()
                            except Exception as peak_record_error:
                                logger.debug(
                                    f"Bot {bot_id}: Could not record peak protection data: {peak_record_error}"
                                )
"""

# ============================================================================
# CHANGE 4: CHECK BEFORE TRADING (Line ~39950, in "for symbol in symbols:")
# ============================================================================
CHANGE_4_CODE = """
# Inside the "for symbol in symbols:" loop (~line 39950-40000)
# Find this existing code:
                for symbol in symbols:
                    if bot_stop_flags.get(bot_id, False):
                        break

                    symbol_is_open, symbol_market_status = market_status_by_symbol.get(...)
                    if not symbol_is_open:
                        last_order_block_reason = f"{symbol} market closed: ..."
                        logger.info(f"⏭️ Bot {bot_id}: Skipping {symbol} - ...")
                        continue

# ADD THIS RIGHT AFTER the market hours check:
                    # Check profit peak protection before trading this symbol
                    if PROFIT_PEAK_PROTECTION_AVAILABLE and PROFIT_PEAK_PROTECTION_ENABLED:
                        should_trade_symbol, peak_reason = should_trade_symbol_with_peak_protection(
                            bot_config,
                            symbol,
                        )
                        if not should_trade_symbol:
                            last_order_block_reason = peak_reason
                            logger.info(f"⏭️ Bot {bot_id}: {peak_reason}")
                            continue
"""

# ============================================================================
# CHANGE 5: ADJUST POSITION SIZE (Line ~40300-40400, when calculating volume)
# ============================================================================
CHANGE_5_CODE = """
# Find where trade volume is calculated (~line 40300-40400)
# Current code pattern:
                        calculated_volume = ...  # Normal volume calculation
                        trade_params = {
                            'symbol': symbol,
                            'volume': calculated_volume,
                            # ... other params ...
                        }

# MODIFY to apply recovery mode adjustment:
                        # Calculate base volume
                        calculated_volume = ...  # Normal volume calculation
                        
                        # Apply recovery mode position size reduction if needed
                        calculated_volume_with_recovery = calculated_volume
                        if PROFIT_PEAK_PROTECTION_AVAILABLE and PROFIT_PEAK_PROTECTION_ENABLED:
                            try:
                                recovery_mode = bot_config.get('symbolRecoveryMode', {}).get(symbol, {})
                                if recovery_mode.get('active'):
                                    recovery_wins = recovery_mode.get('consecutive_wins', 0)
                                    calculated_volume_with_recovery = calculate_recovery_position_size(
                                        calculated_volume,
                                        recovery_mode_active=True,
                                        recovery_win_count=recovery_wins,
                                        recovery_required_wins=PROFIT_PEAK_PROTECTION_RECOVERY_WINS_REQUIRED,
                                    )
                                    if calculated_volume_with_recovery < calculated_volume:
                                        logger.info(
                                            f"📉 Bot {bot_id}: Reduced {symbol} position size from "
                                            f"{calculated_volume:.4f} to {calculated_volume_with_recovery:.4f} "
                                            f"(recovery mode: {recovery_wins}/{PROFIT_PEAK_PROTECTION_RECOVERY_WINS_REQUIRED} wins)"
                                        )
                            except Exception as e:
                                logger.debug(f"Bot {bot_id}: Could not apply recovery size adjustment: {e}")
                        
                        trade_params = {
                            'symbol': symbol,
                            'volume': calculated_volume_with_recovery,  # Use adjusted volume
                            # ... other params ...
                        }
"""

# ============================================================================
# CHANGE 6: LOG STATUS (Line ~40500-40600, periodic logging)
# ============================================================================
CHANGE_6_CODE = """
# In the main trading loop, add periodic status logging (~line 40500-40600)
# Find a good spot to add this after the symbol iteration completes:

                # Log profit protection status periodically (every 10 cycles)
                if PROFIT_PEAK_PROTECTION_AVAILABLE and PROFIT_PEAK_PROTECTION_ENABLED and (trade_cycle % 10 == 0):
                    try:
                        protection_summary = format_symbol_protection_summary(bot_config)
                        if protection_summary and "STATUS" in protection_summary:
                            logger.info(protection_summary)
                    except Exception as e:
                        logger.debug(f"Bot {bot_id}: Could not format protection summary: {e}")
"""

# ============================================================================
# IMPLEMENTATION STEPS
# ============================================================================

IMPLEMENTATION_STEPS = """
STEP-BY-STEP IMPLEMENTATION:

1. BACKUP:
   cp multi_broker_backend_updated.py multi_broker_backend_updated.py.backup

2. FIND AND COPY:
   - Open multi_broker_backend_updated.py in VS Code
   - CHANGE 1: Find "import" section (line ~1-50)
   - CHANGE 2: Find config section (line ~400-500)
   - CHANGE 3: Find trade closing (line ~10520)
   - CHANGE 4: Find symbol loop (line ~39950)
   - CHANGE 5: Find volume calculation (line ~40300)
   - CHANGE 6: Find periodic logging spot (line ~40500)

3. MAKE EDITS:
   - Copy CHANGE_1_CODE → Paste at "import" section
   - Copy CHANGE_2_CODE → Paste at config section
   - Copy CHANGE_3_CODE → Paste after trade closes
   - Copy CHANGE_4_CODE → Paste in symbol loop
   - Copy CHANGE_5_CODE → Paste volume adjustment
   - Copy CHANGE_6_CODE → Paste periodic logging

4. TEST SYNTAX:
   python -m py_compile multi_broker_backend_updated.py

5. TEST LOGIC:
   python -c "from fix_profit_peak_erosion import *; print('✅ Module imports OK')"

6. START SINGLE BOT:
   - Restart backend
   - Start 1 bot with ETH/SOL
   - Watch logs for "PEAK DETECTED" messages

7. MONITOR:
   - Let run for 24 hours
   - Check for cooldown activations
   - Verify recovery mode behavior
   - Confirm position size reductions

8. SCALE:
   - If good after 24h, restart all bots
   - Feature activates automatically

TROUBLESHOOTING:

If "PROFIT_PEAK_PROTECTION_AVAILABLE" is False:
  → fix_profit_peak_erosion.py is not in same directory
  → Check import error in logs
  → Copy fix_profit_peak_erosion.py to backend directory

If no peaks detected:
  → Reduce PROFIT_PEAK_PROTECTION_MIN_PEAK_PROFIT to $0.20
  → Reduce PROFIT_PEAK_PROTECTION_DECLINE_THRESHOLD to $0.02

If cooldowns too aggressive:
  → Reduce PROFIT_PEAK_PROTECTION_COOLDOWN_MINUTES to 5-10

If position sizes too small:
  → Increase PROFIT_PEAK_PROTECTION_RECOVERY_SIZE_PERCENT to 0.65-0.75

DISABLE IF NEEDED:
  Set PROFIT_PEAK_PROTECTION_ENABLED = False
  Restart backend
  No data loss, just stops using protection
"""

print("""
================================================================================
                    PROFIT PEAK PROTECTION - QUICK REFERENCE
================================================================================

This document contains the exact code changes needed for implementation.

IMPORTANT: Read INTEGRATION_GUIDE_profit_peak_protection.md first!
          Run fix_profit_peak_erosion.py to test the core logic!

6 CHANGES NEEDED (total ~85 lines):
""")

print("1. ADD IMPORT")
print("   " + "-"*70)
print(CHANGE_1_CODE)

print("\n2. ADD CONFIG FLAGS")
print("   " + "-"*70)
print(CHANGE_2_CODE)

print("\n3. RECORD TRADE")
print("   " + "-"*70)
print("(See CHANGE_3_CODE in this file)")

print("\n4. CHECK BEFORE TRADING")
print("   " + "-"*70)
print("(See CHANGE_4_CODE in this file)")

print("\n5. ADJUST POSITION SIZE")
print("   " + "-"*70)
print("(See CHANGE_5_CODE in this file)")

print("\n6. LOG STATUS")
print("   " + "-"*70)
print("(See CHANGE_6_CODE in this file)")

print("\n" + "="*80)
print(IMPLEMENTATION_STEPS)
print("="*80)

print("\nSUMMARY:")
print("  ✅ fix_profit_peak_erosion.py - Core engine (created)")
print("  ✅ INTEGRATION_GUIDE_profit_peak_protection.md - Reference (created)")
print("  ⚠️  multi_broker_backend_updated.py - REQUIRES 6 manual edits")
print("\nNext: Make the 6 edits above, then test with 1 bot for 24 hours")
