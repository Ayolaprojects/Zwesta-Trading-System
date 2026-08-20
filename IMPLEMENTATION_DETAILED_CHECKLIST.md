# Zwesta Trading Backend - Implementation Checklist
**Date**: 2026-08-13  
**File**: `multi_broker_backend_updated.py`  
**Total Changes**: ~400 lines across 6 sections

---

## 📍 Location Reference Guide

### Current Code Locations
- **Top Movers Functions**: Lines 34758-35040
- **Profit Protection Config**: Lines 35005-35150  
- **Bot Config Update**: Lines 26511-26950
- **Trading Loop**: Lines ~5000+ (search for `continuous_bot_trading_loop`)
- **API Endpoints**: Lines 6000+ (search for `@app.route`)
- **Database Init**: Lines ~300+ (search for `init_database()`)

### Database Tables
- `user_bots` - Store bot configuration
- `broker_credentials` - Store broker access
- `trades` - Store completed trades
- `wallet_transactions` - Store transaction history

---

## 🔧 SECTION 1: Top Movers - Exness Mapping

### File: `multi_broker_backend_updated.py`

**Line ~34912**: Replace entire `_map_binance_top_mover_symbol_to_broker()` function

```python
# BEFORE: Current implementation ~20 lines
def _map_binance_top_mover_symbol_to_broker(symbol: str, broker_name: str) -> Optional[str]:
    # ... only handles Binance & basic Exness

# AFTER: Enhanced implementation ~80 lines
def _map_binance_top_mover_symbol_to_broker(symbol: str, broker_name: str) -> Optional[str]:
    # See FEATURE_IMPLEMENTATION_GUIDE.md for full code
```

**Changes Needed**:
- [ ] Add `exness_mapping` dictionary (20 lines)
- [ ] Add SYMBOL_MAPPING lookup (5 lines)
- [ ] Add fallback to base+'USD' (3 lines)
- [ ] Verify symbol in VALID_SYMBOLS (3 lines)

---

**Line ~34750**: Add new configuration constants

```python
# ADD AFTER line 34748:
_EXNESS_TOP_MOVERS_CONFIG = {
    'min_change_pct': 0.6,        # Lower threshold for FX pairs
    'min_volume_usdt': 20_000_000, # High volume for FX
    'max_symbols': 15,
    'preferred_pairs': [
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',
        'NZDUSD', 'USDCAD', 'USDZAR',
        'BTCUSD', 'ETHUSD', 'XAUUSD',
    ]
}
```

**Changes Needed**:
- [ ] Add `_EXNESS_TOP_MOVERS_CONFIG` (8 lines)

---

**Line ~35040**: Add new function `get_top_movers_for_broker()`

```python
# ADD AFTER current top movers functions (~50 lines):
def get_top_movers_for_broker(bot_config, broker_name=None):
    # See FEATURE_IMPLEMENTATION_GUIDE.md for full code
```

**Changes Needed**:
- [ ] Add function `get_top_movers_for_broker()` (50 lines)
- [ ] Handle Binance path (10 lines)
- [ ] Handle Exness path with FX threshold (30 lines)
- [ ] Return formatted candidates (10 lines)

---

**Line ~6000** (or nearby `@app.route` section): Add API endpoint

```python
# ADD NEW ENDPOINT (~40 lines):
@app.route('/api/bot/<bot_id>/top-movers', methods=['GET'])
@require_session
def get_bot_top_movers(bot_id):
    # See FEATURE_IMPLEMENTATION_GUIDE.md for full code
```

**Changes Needed**:
- [ ] Add `@app.route` decorator (2 lines)
- [ ] Add authorization check (5 lines)
- [ ] Call `get_top_movers_for_broker()` (3 lines)
- [ ] Return JSON response (5 lines)

---

### Testing Checklist for Section 1
- [ ] Verify Binance top movers still work
- [ ] Test Exness symbol mapping (EUR, GBP, BTC, XAU)
- [ ] Test with demo Exness account
- [ ] Verify API returns proper JSON
- [ ] Check volume filtering working

---

## 🔧 SECTION 2: Floor Trading

### File: `multi_broker_backend_updated.py`

**Database Schema Change**: Add columns to `user_bots` table

```python
# Find init_database() function (around line ~500-1000)
# ADD to CREATE TABLE user_bots section:

ALTER TABLE user_bots ADD COLUMN floor_trading_enabled BOOLEAN DEFAULT 0;
ALTER TABLE user_bots ADD COLUMN floor_levels TEXT DEFAULT '{}';
ALTER TABLE user_bots ADD COLUMN floor_update_strategy TEXT DEFAULT 'manual';
ALTER TABLE user_bots ADD COLUMN floor_adjustment_percent REAL DEFAULT 1.0;
```

**Changes Needed**:
- [ ] Add `floor_trading_enabled` column (migration)
- [ ] Add `floor_levels` column (JSON text)
- [ ] Add `floor_update_strategy` column
- [ ] Add `floor_adjustment_percent` column

---

**Line ~26698** (bot config defaults): Add floor config defaults

```python
# In update_bot_config() function, find line with:
# effective_data.setdefault('topMoversDirectTrading', ...)

# ADD AFTER that section (~8 lines):
effective_data.setdefault('floorTradingEnabled', bot.get('floorTradingEnabled', False))
effective_data.setdefault('floorLevels', bot.get('floorLevels', {}))
effective_data.setdefault('floorUpdateStrategy', bot.get('floorUpdateStrategy', 'manual'))
effective_data.setdefault('floorAdjustmentPercent', bot.get('floorAdjustmentPercent', 1.0))
```

**Changes Needed**:
- [ ] Add 4 default setdefault() calls (4 lines)

---

**Line ~5000** (before trading loop): Add floor functions

```python
# ADD BEFORE continuous_bot_trading_loop() (~100 lines):

def _should_skip_trade_due_to_floor(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md

def _update_floor_after_close(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md
```

**Changes Needed**:
- [ ] Add `_should_skip_trade_due_to_floor()` (25 lines)
- [ ] Add `_update_floor_after_close()` (40 lines)

---

### Testing Checklist for Section 2
- [ ] Create bot with floor enabled
- [ ] Test trade below floor is blocked
- [ ] Test trade above floor proceeds
- [ ] Test floor updates on profit close
- [ ] Test trailing floor strategy
- [ ] Verify DB persistence

---

## 🔧 SECTION 3: Signal Profit Preservation

### File: `multi_broker_backend_updated.py`

**Line ~26698**: Add signal config defaults

```python
# In update_bot_config(), add (~4 lines):
effective_data.setdefault('signalProfitPreservationEnabled', 
                         bot.get('signalProfitPreservationEnabled', True))
effective_data.setdefault('signalProtectionProfile', bot.get('signalProtectionProfile', 'strict'))
effective_data.setdefault('signalTradeLockMinutes', bot.get('signalTradeLockMinutes', 30))
```

**Changes Needed**:
- [ ] Add 3 default config lines (3 lines)

---

**Line ~5000**: Add signal functions

```python
# ADD BEFORE trading loop (~130 lines):

def _identify_signal_trade_origin(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md

def _apply_signal_profit_protection(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md

def _track_signal_trade_metadata(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md
```

**Changes Needed**:
- [ ] Add `_identify_signal_trade_origin()` (20 lines)
- [ ] Add `_apply_signal_profit_protection()` (50 lines)
- [ ] Add `_track_signal_trade_metadata()` (20 lines)

---

### Testing Checklist for Section 3
- [ ] Create signal-triggered trade
- [ ] Verify strict profile applies
- [ ] Test aggressive profile (longer holds)
- [ ] Test conservative profile (faster locks)
- [ ] Verify signal trade metadata recorded
- [ ] Check protection overrides working

---

## 🔧 SECTION 4: Extended Exness Hold Periods

### File: `multi_broker_backend_updated.py`

**Line ~26698**: Add Exness hold config defaults

```python
# In update_bot_config(), add (~8 lines):
if effective_data.get('isExness'):
    effective_data.setdefault('exnessMinHoldMinutes', bot.get('exnessMinHoldMinutes', 45))
    effective_data.setdefault('exnessMaxHoldMinutes', bot.get('exnessMaxHoldMinutes', 120))
    effective_data.setdefault('exnessSessionCloseHour', bot.get('exnessSessionCloseHour', 22))
else:
    effective_data.setdefault('minHoldMinutes', bot.get('minHoldMinutes', 20))
    effective_data.setdefault('maxHoldMinutes', bot.get('maxHoldMinutes', 45))
```

**Changes Needed**:
- [ ] Add `isExness` detection (1 line)
- [ ] Add Exness hold defaults (4 lines)
- [ ] Add non-Exness hold defaults (2 lines)

---

**Line ~5000**: Add Exness hold functions

```python
# ADD BEFORE trading loop (~150 lines):

def _get_hold_time_limits_for_broker(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md

def _should_extend_hold_for_exness(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md

def _calculate_adaptive_exit_time(...):
    # See FEATURE_IMPLEMENTATION_GUIDE.md
```

**Changes Needed**:
- [ ] Add `_get_hold_time_limits_for_broker()` (25 lines)
- [ ] Add `_should_extend_hold_for_exness()` (35 lines)
- [ ] Add `_calculate_adaptive_exit_time()` (50 lines)

---

### Testing Checklist for Section 4
- [ ] Create Exness bot with default 45-120 min holds
- [ ] Verify short trades exit at 45 min
- [ ] Verify strong trends hold to 120 min
- [ ] Test session close hour enforcement
- [ ] Verify adaptive exit based on trend strength
- [ ] Check non-Exness bots unaffected

---

## 📋 Integration Checklist

### Pre-Implementation
- [ ] Backup current database
- [ ] Backup `multi_broker_backend_updated.py`
- [ ] Create feature branch in git
- [ ] Set up test accounts (demo)

### Implementation Phases
- [ ] **Phase 1**: Top Movers (4-5 hours)
- [ ] **Phase 2**: Floor Trading (5-6 hours)
- [ ] **Phase 3**: Signal Preservation (3-4 hours)
- [ ] **Phase 4**: Exness Holds (3-4 hours)

### Testing
- [ ] Unit test each function
- [ ] Integration test with trading loop
- [ ] API endpoint testing
- [ ] Demo account trading test
- [ ] Database persistence test

### Deployment
- [ ] Code review
- [ ] Staging deployment
- [ ] Production rollout
- [ ] 48-hour monitoring

---

## 📊 Effort Estimation

| Section | Functions | API Endpoints | Lines | Time |
|---------|-----------|---------------|-------|------|
| Top Movers | 1 | 1 | 130 | 4h |
| Floor Trading | 2 | 2 | 150 | 5h |
| Signal Protection | 3 | 1 | 130 | 4h |
| Exness Holds | 3 | 2 | 140 | 4h |
| **TOTAL** | **9** | **6** | **550** | **17h** |

---

**Last Updated**: 2026-08-13  
**Status**: Ready for Implementation  
