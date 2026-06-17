#!/usr/bin/env python3
"""
AUTOMATED IMPLEMENTATION PLAN: Profit Peak Erosion Protection

This script generates the exact code patches needed to integrate profit peak
protection into multi_broker_backend_updated.py.

Run this to see the exact edits needed (no automatic patching - manual review required).
"""

implementation_plan = """
================================================================================
IMPLEMENTATION: Profit Peak Erosion Protection for ETH/SOL/BTC
================================================================================

ROOT CAUSE ANALYSIS:
────────────────────────────────────────────────────────────────────────────────
Problem:
  1. Bot trades ETH, makes profit (e.g., $1.21 cumulative)
  2. Same symbol traded next cycle, but market conditions changed
  3. Subsequent trades on ETH lose money gradually
  4. Profits eroded until losses occur
  5. No mechanism stops or adjusts position size

Result: ETH/SOL/BTC create "profit peak erosion" pattern

Solution: Implement symbol-level profit peak detection + cooldown + recovery mode

================================================================================
CHANGES SUMMARY
================================================================================

Total Lines to Add: ~200-250 lines of integration code
Files to Modify: 1 (multi_broker_backend_updated.py)
New Files: 2 (fix_profit_peak_erosion.py + INTEGRATION_GUIDE)

Impact:
  - Zero breaking changes
  - Backward compatible
  - Gracefully handles bots without tracking data
  - Can be toggled via bot config flag

================================================================================
STEP-BY-STEP IMPLEMENTATION
================================================================================

STEP 1: ADD IMPORT
────────────────────────────────────────────────────────────────────────────────
File: multi_broker_backend_updated.py
Location: Line ~1-50 (with other imports)

ADD THESE IMPORTS:
```python
# Profit peak erosion protection (new feature)
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
```

STEP 2: ADD CONFIGURATION FLAG
────────────────────────────────────────────────────────────────────────────────
File: multi_broker_backend_updated.py
Location: Around line ~400-500 (where bot defaults are set)

ADD THIS CONFIGURATION:
```python
# Feature flags for profit protection
PROFIT_PEAK_PROTECTION_ENABLED = True  # Set to False to disable feature
PROFIT_PEAK_PROTECTION_COOLDOWN_MINUTES = 15  # After peak, cooldown duration
PROFIT_PEAK_PROTECTION_MIN_PEAK_PROFIT = 0.50  # Minimum profit to arm ($)
PROFIT_PEAK_PROTECTION_DECLINE_THRESHOLD = 0.05  # Min decline to trigger ($)
PROFIT_PEAK_PROTECTION_RECOVERY_WINS_REQUIRED = 3  # Wins to graduate recovery
PROFIT_PEAK_PROTECTION_RECOVERY_SIZE_PERCENT = 0.50  # Position size in recovery
```

STEP 3: RECORD TRADE COMPLETION
────────────────────────────────────────────────────────────────────────────────
File: multi_broker_backend_updated.py
Location: Around line ~10520 (where trades close and profit is recorded)

FIND THIS CODE:
```python
if matched_pos:
    trade_profit = matched_pos.get('profit') or matched_pos.get('pnl') or 0
    # ... trade closing logic ...
    trades_placed += 1
```

ADD AFTER trade closes successfully:
```python
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
```

STEP 4: CHECK PEAK PROTECTION BEFORE SYMBOL SELECTION
────────────────────────────────────────────────────────────────────────────────
File: multi_broker_backend_updated.py
Location: Around line ~39950-40000 inside "for symbol in symbols:" loop

FIND THIS CODE:
```python
                for symbol in symbols:
                    if bot_stop_flags.get(bot_id, False):
                        break

                    # Market hours check...
                    symbol_is_open, symbol_market_status = market_status_by_symbol.get(...)
                    if not symbol_is_open:
                        last_order_block_reason = f"{symbol} market closed: ..."
                        logger.info(f"⏭️ Bot {bot_id}: Skipping {symbol} - ...")
                        continue
```

ADD AFTER market hours check:
```python
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
```

STEP 5: ADJUST POSITION SIZE FOR RECOVERY MODE
────────────────────────────────────────────────────────────────────────────────
File: multi_broker_backend_updated.py
Location: Around line ~40300-40400 where trade_params volume is calculated

FIND THIS CODE:
```python
                        # ... calculate volume ...
                        trade_params = {
                            'symbol': symbol,
                            'volume': calculated_volume,
                            # ... other params ...
                        }
```

MODIFY to:
```python
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
                            'volume': calculated_volume_with_recovery,
                            # ... other params ...
                        }
```

STEP 6: LOG PROTECTION STATUS PERIODICALLY
────────────────────────────────────────────────────────────────────────────────
File: multi_broker_backend_updated.py
Location: Around line ~40500-40600 in the main loop

ADD PERIODIC LOGGING (every 10 cycles):
```python
                    # Log profit protection status periodically
                    if PROFIT_PEAK_PROTECTION_AVAILABLE and PROFIT_PEAK_PROTECTION_ENABLED and (trade_cycle % 10 == 0):
                        try:
                            protection_summary = format_symbol_protection_summary(bot_config)
                            if protection_summary and "STATUS" in protection_summary:
                                logger.info(protection_summary)
                        except Exception as e:
                            logger.debug(f"Bot {bot_id}: Could not format protection summary: {e}")
```

================================================================================
BEFORE & AFTER EXAMPLE
================================================================================

BEFORE IMPLEMENTATION:
────────────────────────────────────────────────────────────────────────────────
Cycle 1: ETHUSDT +$0.45 (cumulative: $0.45)
Cycle 2: ETHUSDT +$0.50 (cumulative: $0.95)
Cycle 3: ETHUSDT +$0.26 (cumulative: $1.21) ← Peak reached
Cycle 4: ETHUSDT -$0.15 (cumulative: $1.06) ← DECLINED $0.15
Cycle 5: ETHUSDT -$0.08 (cumulative: $0.98) ← DECLINED $0.23 - NO PROTECTION!
Cycle 6: ETHUSDT -$0.12 (cumulative: $0.86) ← DECLINED $0.35 - LOSSES ACCUMULATE
────────────────────────────────────────────────────────────────────────────────
Final: -$0.35 loss despite $1.21 peak

AFTER IMPLEMENTATION:
────────────────────────────────────────────────────────────────────────────────
Cycle 1: ETHUSDT +$0.45 (cumulative: $0.45)
Cycle 2: ETHUSDT +$0.50 (cumulative: $0.95)
Cycle 3: ETHUSDT +$0.26 (cumulative: $1.21) ← Peak reached
Cycle 4: ETHUSDT -$0.15 (cumulative: $1.06) ← Decline detected!
           ⚠️ PEAK DETECTED! Cooldown activated!
Cycle 5: [ETHUSDT SKIPPED - IN COOLDOWN] → SOLUSDT +$0.42 (diversified!)
Cycle 6: [ETHUSDT SKIPPED - IN COOLDOWN] → BTCUSDT +$0.38
Cycle 7: ETHUSDT +$0.35 (recovery trade, 50% size) ← After cooldown
────────────────────────────────────────────────────────────────────────────────
Final: +$1.95 profit (avoided $0.35 loss + gained diversity)

================================================================================
EXPECTED LOG OUTPUT
================================================================================

When peak is detected:
  ⚠️ Bot 123456: PROFIT PEAK DETECTED on ETHUSDT!
     Peak: $1.21, Declined: $0.35 → Activating 15-minute cooldown

During cooldown:
  ⏭️ Bot 123456: 🔒 Profit peak cooldown for 14m (ETHUSDT) - skipping

During recovery:
  📉 Bot 123456: Reduced ETHUSDT position size from 0.1000 to 0.0500
     (recovery mode: 0/3 wins)

When graduated:
  ✅ Bot 123456: ETHUSDT Recovery mode graduated (3/3 wins)

Periodic status:
  📊 SYMBOL PROFIT PROTECTION STATUS:
     🔒 ETHUSDT: 8m cooldown
     ⚠️ SOLUSDT: Recovery mode (1/3 wins, peak $1.35)
     📈 ETHUSDT: $0.86 cumulative (peak $1.21, declined $0.35)

================================================================================
TESTING CHECKLIST
================================================================================

[ ] Import added successfully (no ModuleNotFoundError)
[ ] Configuration flags set and readable
[ ] Trade profit recorded after close
[ ] Peak detection triggers correctly
[ ] Cooldown blocks symbol re-entry
[ ] Position size reduces in recovery
[ ] Position size restores after graduation
[ ] Logs show protection status
[ ] No errors with bots that don't have tracking data
[ ] Feature works with multiple symbols
[ ] Works with both MT5 and Binance brokers
[ ] Can be disabled via flag without errors

================================================================================
ROLLBACK PROCEDURE
================================================================================

If issues occur:
1. Set PROFIT_PEAK_PROTECTION_ENABLED = False
2. Restart backend and all bots
3. Bot configs will retain tracking data but not use it
4. No data loss, protection just disabled

To fully remove:
1. Delete fix_profit_peak_erosion.py
2. Remove import statement
3. Remove all 6 added code sections
4. Clean up bot_config keys: symbolProfitHistory, symbolPeakDetection, etc.

================================================================================
"""

print(implementation_plan)

# Generate file checklist
print("\n\n" + "="*80)
print("FILES CREATED/MODIFIED:")
print("="*80)

files = {
    "fix_profit_peak_erosion.py": {
        "purpose": "Core profit peak detection engine",
        "functions": [
            "detect_profit_peak()",
            "record_symbol_trade()",
            "should_trade_symbol_with_peak_protection()",
            "calculate_recovery_position_size()",
        ],
        "lines": 350,
        "status": "✅ CREATED",
    },
    "INTEGRATION_GUIDE_profit_peak_protection.md": {
        "purpose": "Detailed integration documentation",
        "sections": [
            "Step 1: Add import",
            "Step 2: Record trades",
            "Step 3: Check peak protection",
            "Step 4: Adjust position size",
            "Step 5: Log status",
        ],
        "lines": 250,
        "status": "✅ CREATED",
    },
    "multi_broker_backend_updated.py": {
        "purpose": "Main trading engine (REQUIRES MANUAL EDITS)",
        "changes": [
            "Add import (1 section, ~5 lines)",
            "Add config flags (1 section, ~5 lines)",
            "Record trade completion (1 section, ~35 lines)",
            "Check peak protection (1 section, ~10 lines)",
            "Adjust position size (1 section, ~20 lines)",
            "Log status (1 section, ~10 lines)",
        ],
        "total_lines": 85,
        "status": "⚠️ REQUIRES MANUAL EDITING",
    },
}

for filename, info in files.items():
    print(f"\n{filename}")
    print(f"  Purpose: {info['purpose']}")
    print(f"  Status: {info['status']}")
    if 'functions' in info:
        print(f"  Functions: {', '.join(info['functions'][:2])} ...")
    if 'changes' in info:
        print(f"  Changes needed: {len(info['changes'])} sections")
    if 'lines' in info and isinstance(info['lines'], int):
        print(f"  Approx lines: {info['lines']}")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("""
1. ✅ Review fix_profit_peak_erosion.py (core engine)
2. ✅ Review INTEGRATION_GUIDE_profit_peak_protection.md (reference)
3. ⚠️  MANUALLY edit multi_broker_backend_updated.py with 6 changes above
4. 🧪 Test with single bot first
5. 📊 Monitor logs for "PEAK DETECTED" messages
6. ✅ Scale to full bot fleet after 24-48 hour validation
7. 📈 Monitor ETH/SOL/BTC profitability improvement
""")
