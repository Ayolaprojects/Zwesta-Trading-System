# Backend Integration Checklist - Profit Peak Protection

## Overview
You need to make **6 code edits** to `multi_broker_backend_updated.py` to integrate the profit peak protection system. Estimated time: **30-45 minutes**.

All code blocks are ready in `QUICK_REFERENCE_code_changes.py` - just copy and paste!

---

## Pre-Integration Checklist

- [ ] **Backup the backend file**
  ```bash
  cp multi_broker_backend_updated.py multi_broker_backend_updated.py.backup
  ```

- [ ] **Verify core engine exists**
  ```bash
  ls -la fix_profit_peak_erosion.py
  # Should show: fix_profit_peak_erosion.py (17,956 bytes)
  ```

- [ ] **Test core engine**
  ```bash
  python fix_profit_peak_erosion.py
  # Should show all tests passing ✅
  ```

---

## EDIT 1: Add Import Statement

**Location:** Lines 1-50 (with other imports)

**Find:** Look for existing import statements at the top of `multi_broker_backend_updated.py`

**Action:** Add this after other imports:
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

**Checklist:**
- [ ] Import added to line 1-50 section
- [ ] Indentation matches surrounding code
- [ ] No syntax errors

---

## EDIT 2: Add Configuration Flags

**Location:** Lines 400-500 (with other config settings)

**Find:** Look for where other configuration flags are defined (search for `ENABLED` or similar config constants)

**Action:** Add this configuration block:
```python
# Profit peak erosion protection configuration
PROFIT_PEAK_PROTECTION_ENABLED = True  # Set to False to disable feature
PROFIT_PEAK_PROTECTION_COOLDOWN_MINUTES = 15  # After peak detected
PROFIT_PEAK_PROTECTION_MIN_PEAK_PROFIT = 0.50  # Minimum profit to arm ($)
PROFIT_PEAK_PROTECTION_DECLINE_THRESHOLD = 0.05  # Min decline to trigger ($)
PROFIT_PEAK_PROTECTION_RECOVERY_WINS_REQUIRED = 3  # Wins to graduate recovery
PROFIT_PEAK_PROTECTION_RECOVERY_SIZE_PERCENT = 0.50  # Position size % in recovery
```

**Checklist:**
- [ ] Configuration flags added
- [ ] All 6 variables defined
- [ ] Values match specification (15m, $0.50, $0.05, 3 wins, 50%)
- [ ] Variables are module-level (not indented)

---

## EDIT 3: Record Trade Completion

**Location:** Lines ~10520 (after trade closes successfully)

**Find:** Search for code like:
```python
if matched_pos:
    trade_profit = matched_pos.get('profit') or matched_pos.get('pnl') or 0
    # ... trade closing code ...
    trades_placed += 1
```

**Action:** Add this RIGHT AFTER the trade closes:
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

**Checklist:**
- [ ] Code added after trade closes
- [ ] Proper indentation (should match surrounding code)
- [ ] Uses `bot_config` variable (verify it exists in that scope)
- [ ] Error handling included (try-except block)

---

## EDIT 4: Check Peak Protection Before Trading

**Location:** Lines ~39950-40000 (in `for symbol in symbols:` loop)

**Find:** Search for code like:
```python
for symbol in symbols:
    if bot_stop_flags.get(bot_id, False):
        break

    # Market hours check...
    symbol_is_open, symbol_market_status = market_status_by_symbol.get(...)
    if not symbol_is_open:
        logger.info(f"⏭️ Bot {bot_id}: Skipping {symbol}...")
        continue
```

**Action:** Add this RIGHT AFTER the market hours check:
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

**Checklist:**
- [ ] Code added after market hours check
- [ ] Proper indentation (should match `for symbol in symbols:` level)
- [ ] Uses `should_trade_symbol_with_peak_protection()` function
- [ ] Continues to next symbol if protection blocks it

---

## EDIT 5: Adjust Position Size for Recovery Mode

**Location:** Lines ~40300-40400 (where trade volume is calculated)

**Find:** Search for code like:
```python
calculated_volume = ...  # Volume calculation
trade_params = {
    'symbol': symbol,
    'volume': calculated_volume,
    # ... other params ...
}
```

**Action:** Modify the volume assignment section:
```python
                        # Calculate base volume
                        calculated_volume = ...  # Your existing volume calculation
                        
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
                            'volume': calculated_volume_with_recovery,  # ← Use adjusted volume
                            # ... other params ...
                        }
```

**Key Change:** Replace `'volume': calculated_volume` with `'volume': calculated_volume_with_recovery`

**Checklist:**
- [ ] Volume calculation preserved
- [ ] Recovery mode check added
- [ ] Position size adjustment applied
- [ ] `trade_params` uses `calculated_volume_with_recovery`
- [ ] Proper indentation

---

## EDIT 6: Log Status Periodically

**Location:** Lines ~40500-40600 (in main trading loop)

**Find:** A good spot after the symbol iteration loop completes, or at the end of the main cycle

**Action:** Add this logging block:
```python
                # Log profit protection status periodically (every 10 cycles)
                if PROFIT_PEAK_PROTECTION_AVAILABLE and PROFIT_PEAK_PROTECTION_ENABLED and (trade_cycle % 10 == 0):
                    try:
                        protection_summary = format_symbol_protection_summary(bot_config)
                        if protection_summary and "STATUS" in protection_summary:
                            logger.info(protection_summary)
                    except Exception as e:
                        logger.debug(f"Bot {bot_id}: Could not format protection summary: {e}")
```

**Note:** `trade_cycle` should be a variable counting the trading loops. If it doesn't exist, you can replace `(trade_cycle % 10 == 0)` with a simple condition like `True` to log every iteration.

**Checklist:**
- [ ] Logging added after symbol iteration
- [ ] Uses `format_symbol_protection_summary()` function
- [ ] Periodic check implemented (every 10 cycles)
- [ ] Error handling included

---

## Post-Integration Validation

### Step 1: Syntax Check
```bash
python -m py_compile multi_broker_backend_updated.py
```
- [ ] No syntax errors reported

### Step 2: Import Verification
```bash
python -c "from fix_profit_peak_erosion import *; print('✅ Module imports OK')"
```
- [ ] Imports successful

### Step 3: Check Both Files Exist
```bash
ls -la fix_profit_peak_erosion.py multi_broker_backend_updated.py
```
- [ ] Both files present in same directory

### Step 4: Test Run (Optional)
Start with a single bot and watch logs:
```bash
# In another terminal, watch logs in real-time
tail -f backend.log | grep "PROFIT_PEAK\|PEAK DETECTED\|recovery"
```
- [ ] Backend starts without errors
- [ ] Bot cycles begin
- [ ] No import errors in logs

---

## Expected Behavior After Integration

### First 2-4 hours:
- Bot trades normally
- No protection activations (unless hitting peak naturally)
- Logs show normal trading

### When profit peak detected:
- Log message: `⚠️ Bot [ID]: PROFIT PEAK DETECTED on ETHUSDT!`
- Symbol added to cooldown
- Position size reduced to 50%

### During cooldown (15 minutes):
- Log message: `⏭️ Bot [ID]: 🔒 Profit peak cooldown for 14m (ETHUSDT)`
- Symbol skipped automatically
- Other symbols trade instead

### After cooldown + 3 winning trades:
- Log message: `✅ Bot [ID]: ETHUSDT Recovery mode graduated (3/3 wins)`
- Position size restored to 100%
- Symbol back to normal trading

---

## Troubleshooting

### Issue: `ImportError: No module named 'fix_profit_peak_erosion'`
**Solution:** 
- Verify `fix_profit_peak_erosion.py` is in the same directory as backend
- Check file exists: `ls -la fix_profit_peak_erosion.py`

### Issue: No "PEAK DETECTED" messages after 24 hours
**Solution:**
- Reduce thresholds:
  - `PROFIT_PEAK_PROTECTION_MIN_PEAK_PROFIT = 0.20` (from 0.50)
  - `PROFIT_PEAK_PROTECTION_DECLINE_THRESHOLD = 0.02` (from 0.05)
- Check if bot making profits at all

### Issue: Cooldowns too aggressive
**Solution:**
- Reduce cooldown time: `PROFIT_PEAK_PROTECTION_COOLDOWN_MINUTES = 5` (from 15)
- Or increase peak requirement: `PROFIT_PEAK_PROTECTION_MIN_PEAK_PROFIT = 1.00` (from 0.50)

### Issue: Position sizes too small
**Solution:**
- Increase recovery size: `PROFIT_PEAK_PROTECTION_RECOVERY_SIZE_PERCENT = 0.65` (from 0.50)

### Issue: Need to disable quickly
**Solution:**
- Set `PROFIT_PEAK_PROTECTION_ENABLED = False`
- Restart backend
- Bot continues normally, no protection active

---

## Rollback Procedure

If something goes wrong:

```bash
# Restore backup
cp multi_broker_backend_updated.py.backup multi_broker_backend_updated.py

# Restart backend
# Feature removed, bots continue normally
```

**No data loss** - bot configs retain tracking data but don't use it.

---

## Success Criteria

After integration, you should see:

✅ No syntax errors on startup
✅ Imports load successfully
✅ Bot cycles begin normally
✅ Within 24-48 hours: "PEAK DETECTED" message appears
✅ Cooldown blocks symbol re-entry
✅ Position size reduces/restores correctly
✅ ETH/SOL/BTC profitability improves
✅ No error messages in logs

---

## Timeline

- **Edits:** 30-45 minutes (6 changes)
- **Testing:** 5 minutes (syntax + import check)
- **Validation:** 24-48 hours (single bot test)
- **Scaling:** Immediate (if test passes, all bots get protection)

**Total to working system: ~1-2 days**

---

## Next Steps

1. ✅ Read this checklist
2. ⏳ Backup backend file
3. ⏳ Apply 6 code edits from QUICK_REFERENCE_code_changes.py
4. ⏳ Run syntax check
5. ⏳ Start single bot test
6. ⏳ Monitor for 24-48 hours
7. ⏳ Scale to all bots if successful
