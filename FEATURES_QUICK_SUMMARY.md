# Zwesta Trading Backend - Quick Feature Summary
**Status**: Implementation Ready  
**Created**: 2026-08-13

## 🎯 Features Overview

### 1️⃣ Top Movers Trading
**What**: Auto-detect and trade high-momentum symbols  
**Where**: Binance & Exness  
**Current**: Binance works, Exness needs symbol mapping  
**Effort**: 2-3 hours (mapping + API endpoint)  
**Code Location**: Line 34912-34942 (symbol mapping)

### 2️⃣ Floor Trading System
**What**: Set minimum price levels - never trade below them  
**Why**: Avoid trading deteriorating setups  
**Example**: EUR/USD floor at 1.0850 blocks entries below that  
**Effort**: 4-5 hours (DB schema + validation + API)  
**Code Location**: New - add to trading loop

### 3️⃣ Signal Profit Preservation
**What**: Apply stricter profit protection to signal-triggered trades  
**Why**: Signals are high-conviction, deserve protection  
**Example**: Lock 50% of peak instead of 30%  
**Effort**: 3-4 hours (identification + rule engine)  
**Code Location**: New - add to position exit logic

### 4️⃣ Extended Exness Hold Periods
**What**: Let Exness trades run longer (45-120 min vs 20-45 min)  
**Why**: FX pairs need more time to develop trends  
**Example**: Strong trend signal → 120-min hold  
**Effort**: 2-3 hours (configuration + adaptive exit)  
**Code Location**: New - add to exit calculation

---

## 📊 Quick Integration Map

```
Bot Creation Flow
    ↓
validate_and_correct_symbols()
    ↓
    ├─→ [NEW] Map Binance pairs to Exness symbols
    └─→ Set floor price, hold times, signal flags
    ↓
Trading Loop
    ├─→ [NEW] Check floor before entry
    ├─→ [NEW] Identify if signal or scanner trade
    ├─→ [NEW] Apply signal-specific protection
    └─→ [NEW] Use adaptive exit times for Exness
    ↓
Close Trade
    ├─→ [NEW] Update floor if profitable
    └─→ Record signal trade metadata
```

---

## 💻 Code Snippets Quick Reference

### Top Movers (add to line ~34912)
```python
exness_mapping = {
    'EUR': 'EURUSD', 'GBP': 'GBPUSD', 'BTC': 'BTCUSD',
    'XAU': 'XAUUSD', 'JPY': 'USDJPY', 'CAD': 'USDCAD',
}
mapped_symbol = exness_mapping.get(base, base + 'USD')
```

### Floor Trading (add to line ~before trading loop)
```python
if _should_skip_trade_due_to_floor(bot_config, symbol, entry_price):
    logger.warning(f"Blocked entry below floor: {symbol}")
    return False
```

### Signal Protection (add to line ~exit calculation)
```python
origin = _identify_signal_trade_origin(bot_config, trade_analysis)
if origin == 'signal':
    protection = _apply_signal_profit_protection(bot_config, position, profit)
```

### Extended Hold (add to line ~exit calculation)
```python
hold_limits = _get_hold_time_limits_for_broker(bot_config)
exit_time = _calculate_adaptive_exit_time(bot_config, position, profit, trend)
```

---

## 🚀 Implementation Order

### Day 1: Setup & Top Movers
1. Review existing code (30 min)
2. Create Exness symbol mapping (1 hour)
3. Create API endpoint (1 hour)
4. Test on demo Exness (1 hour)

### Day 2: Floor Trading
1. Add DB columns (30 min)
2. Create validation functions (1 hour)
3. Create API endpoints (1 hour)
4. Integrate into trading loop (1 hour)
5. Test floor blocking (1 hour)

### Day 3: Signal Protection
1. Create identification function (1 hour)
2. Create protection rules (1 hour)
3. Integrate into exit logic (1 hour)
4. Test on various signals (1 hour)

### Day 4: Exness Hold Periods
1. Create hold calculation (1 hour)
2. Create API endpoints (1 hour)
3. Create adaptive exit logic (1 hour)
4. Full integration test (1 hour)

---

## 📋 Database Changes Needed

```sql
-- Add these columns to user_bots table
ALTER TABLE user_bots ADD COLUMN floor_trading_enabled BOOLEAN DEFAULT 0;
ALTER TABLE user_bots ADD COLUMN floor_levels TEXT DEFAULT '{}';  -- JSON
ALTER TABLE user_bots ADD COLUMN floor_update_strategy TEXT DEFAULT 'manual';

ALTER TABLE user_bots ADD COLUMN signal_profit_preservation_enabled BOOLEAN DEFAULT 1;
ALTER TABLE user_bots ADD COLUMN signal_protection_profile TEXT DEFAULT 'strict';
ALTER TABLE user_bots ADD COLUMN signal_trade_lock_minutes REAL DEFAULT 30;

ALTER TABLE user_bots ADD COLUMN exness_min_hold_minutes REAL DEFAULT 45;
ALTER TABLE user_bots ADD COLUMN exness_max_hold_minutes REAL DEFAULT 120;
ALTER TABLE user_bots ADD COLUMN exness_session_close_hour INTEGER DEFAULT 22;
```

---

## 🔗 API Endpoints Summary

```
NEW ENDPOINTS:

GET  /api/bot/{bot_id}/top-movers
     → Returns available top movers for bot

PUT  /api/bot/{bot_id}/floor-config
GET  /api/bot/{bot_id}/floor-levels
     → Manage floor price settings

PUT  /api/bot/{bot_id}/signal-protection
     → Configure signal profit rules

PUT  /api/bot/{bot_id}/exness-hold-config
GET  /api/bot/{bot_id}/exness-hold-config
     → Manage Exness hold periods
```

---

## 🧪 Testing Commands

```bash
# Test top movers available
curl http://localhost:5000/api/bot/BOT123/top-movers

# Set floor price
curl -X PUT http://localhost:5000/api/bot/BOT123/floor-config \
  -H "Content-Type: application/json" \
  -d '{"floorTradingEnabled": true, "floorLevels": {"EURUSD": 1.0850}}'

# Configure signal protection
curl -X PUT http://localhost:5000/api/bot/BOT123/signal-protection \
  -H "Content-Type: application/json" \
  -d '{"signalProtectionProfile": "strict"}'

# Set Exness hold times
curl -X PUT http://localhost:5000/api/bot/BOT123/exness-hold-config \
  -H "Content-Type: application/json" \
  -d '{"minHoldMinutes": 45, "maxHoldMinutes": 120}'
```

---

## 📈 Expected Performance Impact

| Feature | Profit Impact | Risk Reduction | Effort |
|---------|---------------|-----------------|--------|
| Top Movers | +15-25% | Better liquidity | Medium |
| Floor Trading | Varies | Avoids bad setups | Medium |
| Signal Protection | Minimal | +5-10% protection | High |
| Exness Hold | +20-30% | Better trends | Low |

---

## ⚠️ Key Warnings

1. **Floor Price**: Once set, validates ALL trades - set carefully
2. **Signal Detection**: Relies on confidence score accuracy
3. **Exness Hold**: Don't extend past session close (gaps on Monday)
4. **Database Backup**: Always backup before schema changes

---

## 📚 Related Files

- `FEATURE_IMPLEMENTATION_GUIDE.md` - Full implementation details
- `multi_broker_backend_updated.py` - Main backend file
- `profit_peak_protection_solution.md` - Existing protection system
- `zwesta_backend_notes.md` - Backend configuration notes

---

## ✅ Completion Checklist

### Implementation
- [ ] Day 1: Top Movers (Exness mapping)
- [ ] Day 2: Floor Trading system
- [ ] Day 3: Signal Profit Protection
- [ ] Day 4: Exness Hold Periods

### Testing
- [ ] Demo account testing for all features
- [ ] API endpoint testing
- [ ] Database persistence testing
- [ ] Integration testing with trading loop

### Deployment
- [ ] Code review complete
- [ ] Logging/monitoring in place
- [ ] Rollback plan documented
- [ ] Production deployment

---

**Total Implementation Time**: 10-12 hours of coding  
**Total Testing Time**: 8-10 hours  
**Recommended Timeline**: 5-7 business days

Last updated: 2026-08-13
