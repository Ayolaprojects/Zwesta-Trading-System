# Zwesta Trading Backend - Feature Implementation Guide
**Created**: 2026-08-13  
**Status**: Ready for Implementation  
**Target**: Exness & Binance Enhancements

---

## 📋 Overview

This guide covers implementing 4 interconnected trading features:
1. **Top Movers Trading** - Auto-trade momentum symbols on Exness & Binance
2. **Floor Trading** - Prevent trades below support price levels
3. **Signal Profit Preservation** - Protect profits from signal-triggered trades
4. **Extended Exness Hold Periods** - Longer position hold times for Exness

---

## 🔍 Current Implementation Status

### ✅ Already Working
- Binance top movers fetching (2-minute cache)
- Profit protection system (15+ parameters)
- Signal evaluation engine
- Bot configuration persistence

### ⚠️ What's Missing
- Exness top movers mapping (Binance USDT → Exness symbols)
- Floor price validation
- Signal-specific profit rules
- Exness hold period configuration

---

## 📊 Architecture Overview

```
Bot Creation Flow:
┌─────────────┐
│  API POST   │  /api/bot/create
└─────────────┘
      ↓
┌─────────────────────┐
│ validate_and_correct_symbols()  │ ← Maps symbols to broker format
└─────────────────────┘
      ↓
┌─────────────────────┐
│ Bot Config Struct   │ ← Store: topMovers, floor, signal rules, holdPeriod
└─────────────────────┘
      ↓
┌─────────────────────┐
│ trading_loop()      │ ← Check floor, evaluate signals, apply hold times
└─────────────────────┘
```

---

## 🚀 Implementation Tasks

### **TASK 1: Exness Top Movers Support**

**Status**: Partially done (Binance exists, need Exness mapping)

**Files to Modify**:
1. `multi_broker_backend_updated.py` - Lines 34912-34942

**Code Changes**:

#### 1A. Enhance Symbol Mapping (Line ~34912)

```python
def _map_binance_top_mover_symbol_to_broker(symbol: str, broker_name: str) -> Optional[str]:
    """
    Map Binance USDT pairs to broker-specific symbols.
    
    Examples:
    - Binance: EURUSDT → EURUSD (Exness), EURUSD (XM), EUR/USD (FXCM)
    - Binance: BTCUSDT → BTCUSD (Exness), BTCUSD (XM)
    - Binance: XAUUSDT → XAUUSD (Exness), GOLD (some brokers)
    """
    normalized_broker = canonicalize_broker_name(broker_name or '')
    raw_symbol = str(symbol or '').upper().strip()
    if not raw_symbol:
        return None

    if normalized_broker == 'Binance':
        corrected = validate_and_correct_symbols([raw_symbol], 'Binance')
        return corrected[0] if corrected else None

    if normalized_broker in {'Exness', 'XM', 'XM Global'}:
        if not raw_symbol.endswith('USDT'):
            return None
        
        base = raw_symbol[:-4]  # Strip 'USDT'
        if not base:
            return None
        
        # NEW: Enhanced mapping for Exness/XM
        exness_mapping = {
            'EUR': 'EURUSD',      # EURUSDT → EURUSD
            'GBP': 'GBPUSD',      # GBPUSDT → GBPUSD  
            'JPY': 'USDJPY',      # JPYUSDT → USDJPY (reverse pair)
            'CHF': 'USDCHF',      # CHFUSDT → USDCHF (reverse pair)
            'AUD': 'AUDUSD',      # AUDUSD → AUDUSD
            'NZD': 'NZDUSD',      # NZDUSD → NZDUSD
            'CAD': 'USDCAD',      # CADUSDT → USDCAD
            'ZAR': 'USDZAR',      # ZARUSDT → USDZAR
            'SGD': 'USDSGD',      # SGDUSDT → USDSGD
            'INR': 'USDINR',      # INRUSDT → USDINR
            'CNY': 'USDCNY',      # CNYUSDT → USDCNY
            'HKD': 'USDHKD',      # HKDUSDT → USDHKD
            'BTC': 'BTCUSD',      # BTCUSDT → BTCUSD
            'ETH': 'ETHUSD',      # ETHUSDT → ETHUSD
            'XAU': 'XAUUSD',      # XAUUSDT → XAUUSD (Gold)
            'XAG': 'XAGUSD',      # XAGUSDT → XAGUSD (Silver)
            'OIL': 'UKOIL',       # OILUSDT → UKOIL (Brent Oil)
            'NGAS': 'NGAS',       # Natural Gas (if available)
        }
        
        mapped_base = exness_mapping.get(base, base + 'USD')
        candidate_symbol = str(mapped_base).upper()
        
        if candidate_symbol in VALID_SYMBOLS:
            return f"{candidate_symbol}m"
        return None

    if normalized_broker == 'FXCM':
        # FXCM expects format: EUR/USD
        if not raw_symbol.endswith('USDT'):
            return None
        base = raw_symbol[:-4]
        return f"{base}/USD" if base else None

    return None


# NEW: Exness-specific top movers configuration
_EXNESS_TOP_MOVERS_CONFIG = {
    'min_change_pct': 0.6,        # Lower threshold for FX pairs
    'min_volume_usdt': 20_000_000, # High volume for FX
    'max_symbols': 15,
    'preferred_pairs': [
        'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD',  # Major pairs
        'NZDUSD', 'USDCAD', 'USDZAR',             # Minor pairs
        'BTCUSD', 'ETHUSD', 'XAUUSD',             # Crypto & metals
    ]
}

def get_top_movers_for_broker(
    bot_config: Dict[str, Any],
    broker_name: str = None,
) -> List[Dict[str, Any]]:
    """
    Get top movers appropriate for the broker.
    
    Binance: 3% change, spot/futures
    Exness/XM: 0.6% change, FX-adjusted
    """
    broker = canonicalize_broker_name(
        broker_name or bot_config.get('brokerName') or 'Binance'
    )
    
    is_futures = str(bot_config.get('marketType') or '').lower().startswith('futures')
    
    if broker == 'Binance':
        return _get_top_movers_direct_trade_candidates(
            bot_config,
            spot=not is_futures,
            broker_name=broker,
            include_fx=False,
        )
    
    elif broker in {'Exness', 'XM', 'XM Global'}:
        # Exness: use FX threshold
        movers = _fetch_binance_top_movers_with_data(
            spot=True,
            min_change_pct=_EXNESS_TOP_MOVERS_CONFIG['min_change_pct'],
            min_volume_usdt=_EXNESS_TOP_MOVERS_CONFIG['min_volume_usdt'],
            max_symbols=_EXNESS_TOP_MOVERS_CONFIG['max_symbols'],
        )
        
        open_positions = bot_config.get('open_positions') or {}
        open_symbols = {
            str(p.get('symbol') or '').upper()
            for p in open_positions.values()
            if isinstance(p, dict)
        } if isinstance(open_positions, dict) else set()
        
        candidates = []
        for sym, data in movers.items():
            target_symbol = _map_binance_top_mover_symbol_to_broker(sym, broker)
            if not target_symbol or target_symbol.upper() in open_symbols:
                continue
            
            candidates.append({
                'symbol': target_symbol,
                'direction': data['direction'],
                'pct_change': data['pct_change'],
                'volume_usdt': data['volume_usdt'],
                'last_price': data['last_price'],
                'source_symbol': sym,
                'broker': broker,
            })
        
        return candidates
    
    return []
```

**API Endpoint** (add after line ~26000):

```python
@app.route('/api/bot/<bot_id>/top-movers', methods=['GET'])
@require_session
def get_bot_top_movers(bot_id):
    """Get available top movers for this bot."""
    try:
        user_id = request.user_id
        bot = active_bots.get(bot_id)
        
        if not bot or bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        if not bot.get('topMoversEnabled', False):
            return jsonify({
                'success': False, 
                'error': 'Top movers not enabled for this bot'
            }), 400
        
        movers = get_top_movers_for_broker(bot)
        
        return jsonify({
            'success': True,
            'top_movers': movers,
            'count': len(movers),
            'broker': bot.get('brokerName', 'Unknown'),
            'cached_at': datetime.now().isoformat(),
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching top movers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### **TASK 2: Floor Trading System**

**Status**: Needs implementation

**Database Schema Change** (add to `init_database()`):

```python
# Add these columns to user_bots table:
# - floor_trading_enabled (BOOLEAN DEFAULT 0)
# - floor_price (REAL DEFAULT 0.0)
# - floor_currency (TEXT DEFAULT 'USD')
# - floor_update_strategy (TEXT DEFAULT 'manual')  # 'manual', 'profit_close', 'trailing'
# - floor_adjustment_percent (REAL DEFAULT 1.0)    # Adjust floor by 1% above close
```

**Configuration in Bot** (update `update_bot_config()` around line 26698):

```python
# In the effective_data.setdefault() section:
effective_data.setdefault('floorTradingEnabled', bot.get('floorTradingEnabled', False))
effective_data.setdefault('floorPrice', bot.get('floorPrice', 0.0))
effective_data.setdefault('floorCurrency', bot.get('floorCurrency', 'USD'))
effective_data.setdefault('floorUpdateStrategy', bot.get('floorUpdateStrategy', 'manual'))
effective_data.setdefault('floorAdjustmentPercent', bot.get('floorAdjustmentPercent', 1.0))
```

**Floor Validation Function** (add before trading loop):

```python
def _should_skip_trade_due_to_floor(bot_config: Dict[str, Any], symbol: str, entry_price: float) -> bool:
    """
    Check if entry price is below the configured floor.
    
    Returns True if:
    - Floor trading is enabled
    - AND symbol has a floor price set
    - AND entry_price < floor_price
    """
    if not bot_config.get('floorTradingEnabled', False):
        return False
    
    symbol_upper = str(symbol or '').upper()
    floor_levels = bot_config.get('floorLevels', {})  # {symbol: price}
    
    if symbol_upper not in floor_levels:
        return False
    
    floor_price = float(floor_levels[symbol_upper] or 0.0)
    if floor_price <= 0:
        return False
    
    entry_price_float = float(entry_price or 0.0)
    
    if entry_price_float < floor_price:
        logger.warning(
            f"[FLOOR GUARD] Skipping {symbol} entry at {entry_price_float} "
            f"(below floor {floor_price})"
        )
        return True
    
    return False


def _update_floor_after_close(bot_config: Dict[str, Any], symbol: str, closed_price: float) -> None:
    """
    Update floor price after a profitable close.
    
    Strategies:
    - 'manual': User sets manually, no auto-update
    - 'profit_close': Set floor to 1% below close on profit
    - 'trailing': Set floor to trailing stop level
    """
    if not bot_config.get('floorTradingEnabled', False):
        return
    
    strategy = str(bot_config.get('floorUpdateStrategy', 'manual')).lower()
    if strategy == 'manual':
        return  # Don't auto-update
    
    symbol_upper = str(symbol or '').upper()
    floor_levels = bot_config.setdefault('floorLevels', {})
    adjustment_pct = float(bot_config.get('floorAdjustmentPercent', 1.0)) / 100.0
    
    closed_price_float = float(closed_price or 0.0)
    
    if strategy == 'profit_close':
        # Set floor to 1% below close price on profitable close
        new_floor = closed_price_float * (1 - adjustment_pct)
        floor_levels[symbol_upper] = round(new_floor, 8)
        
        logger.info(
            f"[FLOOR UPDATE] {symbol} closed at {closed_price_float}; "
            f"floor updated to {new_floor}"
        )
    
    elif strategy == 'trailing':
        # Trailing stop: floor only moves up, never down
        current_floor = floor_levels.get(symbol_upper, 0.0)
        new_floor = closed_price_float * (1 - adjustment_pct)
        
        if new_floor > current_floor:
            floor_levels[symbol_upper] = round(new_floor, 8)
            logger.info(
                f"[FLOOR TRAILING] {symbol}: floor {current_floor} → {new_floor}"
            )
```

**API Endpoint for Floor Management** (add around line 26000):

```python
@app.route('/api/bot/<bot_id>/floor-config', methods=['PUT'])
@require_session
def update_floor_config(bot_id):
    """Configure floor trading for a bot."""
    try:
        user_id = request.user_id
        data = request.json or {}
        
        bot = active_bots.get(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        # Update floor configuration
        bot['floorTradingEnabled'] = _coerce_bool(data.get('floorTradingEnabled', False), False)
        bot['floorUpdateStrategy'] = str(data.get('floorUpdateStrategy', 'manual')).lower()
        bot['floorAdjustmentPercent'] = float(data.get('floorAdjustmentPercent', 1.0))
        
        # Update floor prices per symbol
        floor_levels = data.get('floorLevels', {})  # {symbol: price}
        if isinstance(floor_levels, dict):
            bot['floorLevels'] = {
                str(k).upper(): float(v)
                for k, v in floor_levels.items()
                if v is not None
            }
        
        # Persist to DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_bots
            SET configuration = ?
            WHERE bot_id = ? AND user_id = ?
        ''', (json.dumps(bot), bot_id, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Floor configuration updated',
            'floor_enabled': bot['floorTradingEnabled'],
            'floor_levels': bot.get('floorLevels', {}),
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating floor config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot/<bot_id>/floor-levels', methods=['GET'])
@require_session
def get_floor_levels(bot_id):
    """Get current floor levels for a bot."""
    try:
        user_id = request.user_id
        bot = active_bots.get(bot_id)
        
        if not bot or bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        return jsonify({
            'success': True,
            'floor_enabled': bot.get('floorTradingEnabled', False),
            'floor_levels': bot.get('floorLevels', {}),
            'update_strategy': bot.get('floorUpdateStrategy', 'manual'),
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching floor levels: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### **TASK 3: Signal Profit Preservation**

**Status**: Needs implementation

**Configuration** (add to bot config):

```python
# In update_bot_config() around line 26698:
effective_data.setdefault('signalProfitPreservationEnabled', 
                         bot.get('signalProfitPreservationEnabled', True))
effective_data.setdefault('signalTradeLockMinutes', bot.get('signalTradeLockMinutes', 30))
effective_data.setdefault('signalProfitTargetPercent', bot.get('signalProfitTargetPercent', 2.0))
effective_data.setdefault('signalProtectionProfile', bot.get('signalProtectionProfile', 'strict'))
```

**Identify Signal-Triggered Trades**:

```python
def _identify_signal_trade_origin(bot_config: Dict[str, Any], trade_analysis: Dict[str, Any]) -> str:
    """
    Identify if this trade came from a signal or scanner.
    
    Returns: 'signal', 'scanner', 'top_mover', or 'manual'
    """
    # Check if there's a signal_source in the trade analysis
    signal_source = trade_analysis.get('signal_source', '')
    if signal_source:
        return signal_source
    
    # Check confidence level - signals typically have confidence > 70
    confidence = float(trade_analysis.get('confidence', 0))
    if confidence > 70:
        return 'signal'
    
    # Check if from top movers
    if trade_analysis.get('from_top_movers', False):
        return 'top_mover'
    
    return 'scanner'


def _apply_signal_profit_protection(
    bot_config: Dict[str, Any],
    position: Dict[str, Any],
    current_profit: float,
    trade_origin: str,
) -> Dict[str, Any]:
    """
    Apply stricter profit protection for signal trades.
    
    Signal trades get:
    - Faster profit locks (50% of peak instead of 70%)
    - Wider trailing stops (20% instead of 10%)
    - Longer hold time (don't force close early)
    - Skip rotation cooldowns
    """
    if trade_origin != 'signal':
        return {}  # Return empty to use default protection
    
    if not bot_config.get('signalProfitPreservationEnabled', True):
        return {}
    
    # Build signal-specific protection override
    signal_protection = {
        'breakEvenActivationShare': 0.50,    # Lock at 50% of peak (vs 30% default)
        'retraceClosePercent': 20.0,         # Wider trail (20% vs 10%)
        'minimumHoldMinutes': 45.0,          # Longer hold (vs 20 min)
        'neverNegativeAfterProfitEnabled': True,
        'neverNegativeActivationProfit': 2.0,  # Stricter
    }
    
    profile = str(bot_config.get('signalProtectionProfile', 'strict')).lower()
    
    if profile == 'aggressive':
        # Less protection - let signals run longer
        signal_protection.update({
            'breakEvenActivationShare': 0.40,
            'retraceClosePercent': 25.0,
            'minimumHoldMinutes': 60.0,
        })
    elif profile == 'conservative':
        # More protection - lock profit faster
        signal_protection.update({
            'breakEvenActivationShare': 0.60,
            'retraceClosePercent': 15.0,
            'minimumHoldMinutes': 30.0,
        })
    
    return signal_protection


def _track_signal_trade_metadata(
    bot_config: Dict[str, Any],
    position: Dict[str, Any],
    trade_origin: str,
) -> None:
    """
    Record signal trade metadata for analysis.
    """
    if trade_origin != 'signal':
        return
    
    signal_trades = bot_config.setdefault('_signal_trade_history', {})
    ticket = str(position.get('ticket', ''))
    
    signal_trades[ticket] = {
        'opened_at': datetime.now().isoformat(),
        'symbol': position.get('symbol'),
        'entry_price': position.get('entry_price'),
        'origin': trade_origin,
    }
    
    # Keep only last 50 signal trades
    if len(signal_trades) > 50:
        oldest = min(signal_trades.keys())
        del signal_trades[oldest]
```

**API Endpoint for Signal Protection**:

```python
@app.route('/api/bot/<bot_id>/signal-protection', methods=['PUT'])
@require_session
def configure_signal_protection(bot_id):
    """Configure signal-specific profit protection."""
    try:
        user_id = request.user_id
        data = request.json or {}
        
        bot = active_bots.get(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        bot['signalProfitPreservationEnabled'] = _coerce_bool(
            data.get('signalProfitPreservationEnabled', True), True
        )
        bot['signalProtectionProfile'] = str(
            data.get('signalProtectionProfile', 'strict')
        ).lower()
        bot['signalTradeLockMinutes'] = float(
            data.get('signalTradeLockMinutes', 30)
        )
        bot['signalProfitTargetPercent'] = float(
            data.get('signalProfitTargetPercent', 2.0)
        )
        
        return jsonify({
            'success': True,
            'message': 'Signal protection configured',
            'profile': bot['signalProtectionProfile'],
        }), 200
        
    except Exception as e:
        logger.error(f"Error configuring signal protection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

### **TASK 4: Extended Exness Hold Periods**

**Status**: Needs implementation

**Configuration**:

```python
# In update_bot_config() around line 26698:
effective_data.setdefault('isExness', 
    canonicalize_broker_name(broker_name) in {'Exness', 'XM', 'XM Global'})

# Exness-specific hold times
if effective_data.get('isExness'):
    effective_data.setdefault('exnessMinHoldMinutes', bot.get('exnessMinHoldMinutes', 45))
    effective_data.setdefault('exnessMaxHoldMinutes', bot.get('exnessMaxHoldMinutes', 120))
    effective_data.setdefault('exnessSessionCloseHour', bot.get('exnessSessionCloseHour', 22))
else:
    effective_data.setdefault('minHoldMinutes', bot.get('minHoldMinutes', 20))
    effective_data.setdefault('maxHoldMinutes', bot.get('maxHoldMinutes', 45))
```

**Hold Period Management Function**:

```python
def _get_hold_time_limits_for_broker(bot_config: Dict[str, Any]) -> Dict[str, float]:
    """
    Get min/max hold times based on broker.
    
    Exness: Longer holds (45-120 min) to capture FX trends
    Binance: Standard holds (20-45 min) for quick momentum
    """
    broker_name = canonicalize_broker_name(
        bot_config.get('brokerName', 'Binance')
    )
    
    if broker_name in {'Exness', 'XM', 'XM Global'}:
        return {
            'min_minutes': float(bot_config.get('exnessMinHoldMinutes', 45)),
            'max_minutes': float(bot_config.get('exnessMaxHoldMinutes', 120)),
            'session_close_hour': int(bot_config.get('exnessSessionCloseHour', 22)),
        }
    
    return {
        'min_minutes': float(bot_config.get('minHoldMinutes', 20)),
        'max_minutes': float(bot_config.get('maxHoldMinutes', 45)),
        'session_close_hour': None,
    }


def _should_extend_hold_for_exness(
    bot_config: Dict[str, Any],
    position: Dict[str, Any],
    current_profit: float,
    profit_percentage: float,
) -> bool:
    """
    Determine if we should extend hold time for Exness position.
    
    Extend if:
    - Broker is Exness/XM
    - Profit is positive but small (1-5%)
    - Position held < max_hold time
    - Not near session close
    """
    broker_name = canonicalize_broker_name(
        bot_config.get('brokerName', '')
    )
    
    if broker_name not in {'Exness', 'XM', 'XM Global'}:
        return False
    
    # Only extend if profit is positive but modest (1-5%)
    if profit_percentage < 1.0 or profit_percentage > 5.0:
        return False
    
    hold_limits = _get_hold_time_limits_for_broker(bot_config)
    open_time = position.get('open_time')
    if not open_time:
        return False
    
    hold_minutes = (datetime.now() - open_time).total_seconds() / 60
    if hold_minutes >= hold_limits['max_minutes']:
        return False
    
    # Check session close hour
    session_close_hour = hold_limits.get('session_close_hour')
    if session_close_hour:
        current_hour = datetime.now().hour
        if current_hour >= session_close_hour:
            return False  # Close positions near end of session
    
    return True


def _calculate_adaptive_exit_time(
    bot_config: Dict[str, Any],
    position: Dict[str, Any],
    current_profit: float,
    trend_strength: float = 50.0,
) -> Optional[datetime]:
    """
    Calculate adaptive exit time for Exness positions.
    
    Longer hold if:
    - Trend is strong (signal > 70)
    - Profit is building gradually (not explosive)
    - No session close approaching
    """
    broker_name = canonicalize_broker_name(
        bot_config.get('brokerName', '')
    )
    
    if broker_name not in {'Exness', 'XM', 'XM Global'}:
        return None
    
    hold_limits = _get_hold_time_limits_for_broker(bot_config)
    
    # Calculate exit time based on trend strength
    # Strong trend (>70) = max hold time
    # Weak trend (<50) = min hold time  
    # Medium trend = scale between min and max
    
    strength_ratio = max(0, min(1, (trend_strength - 40) / 60))  # 0-1 range
    
    base_min = hold_limits['min_minutes']
    base_max = hold_limits['max_minutes']
    
    recommended_hold = base_min + (base_max - base_min) * strength_ratio
    
    open_time = position.get('open_time')
    if not open_time:
        return None
    
    exit_time = open_time + timedelta(minutes=recommended_hold)
    
    # Don't hold past session close
    session_close_hour = hold_limits.get('session_close_hour')
    if session_close_hour:
        close_time = exit_time.replace(hour=session_close_hour, minute=0, second=0)
        if exit_time > close_time:
            exit_time = close_time
    
    return exit_time
```

**API Endpoint for Exness Hold Configuration**:

```python
@app.route('/api/bot/<bot_id>/exness-hold-config', methods=['PUT'])
@require_session
def configure_exness_hold_periods(bot_id):
    """Configure extended hold periods for Exness."""
    try:
        user_id = request.user_id
        data = request.json or {}
        
        bot = active_bots.get(bot_id)
        if not bot or bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        broker_name = canonicalize_broker_name(
            bot.get('brokerName', '')
        )
        if broker_name not in {'Exness', 'XM', 'XM Global'}:
            return jsonify({
                'success': False,
                'error': 'This endpoint is for Exness/XM bots only'
            }), 400
        
        bot['exnessMinHoldMinutes'] = float(data.get('minHoldMinutes', 45))
        bot['exnessMaxHoldMinutes'] = float(data.get('maxHoldMinutes', 120))
        bot['exnessSessionCloseHour'] = int(data.get('sessionCloseHour', 22))
        bot['adaptiveExitEnabled'] = _coerce_bool(
            data.get('adaptiveExitEnabled', True), True
        )
        
        return jsonify({
            'success': True,
            'message': 'Exness hold configuration updated',
            'min_hold': bot['exnessMinHoldMinutes'],
            'max_hold': bot['exnessMaxHoldMinutes'],
            'session_close': bot['exnessSessionCloseHour'],
        }), 200
        
    except Exception as e:
        logger.error(f"Error configuring Exness hold: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot/<bot_id>/exness-hold-config', methods=['GET'])
@require_session
def get_exness_hold_config(bot_id):
    """Get current Exness hold configuration."""
    try:
        user_id = request.user_id
        bot = active_bots.get(bot_id)
        
        if not bot or bot.get('user_id') != user_id:
            return jsonify({'success': False, 'error': 'Bot not found'}), 404
        
        broker_name = canonicalize_broker_name(
            bot.get('brokerName', '')
        )
        if broker_name not in {'Exness', 'XM', 'XM Global'}:
            return jsonify({
                'success': False,
                'error': 'This endpoint is for Exness/XM bots only'
            }), 400
        
        return jsonify({
            'success': True,
            'min_hold_minutes': bot.get('exnessMinHoldMinutes', 45),
            'max_hold_minutes': bot.get('exnessMaxHoldMinutes', 120),
            'session_close_hour': bot.get('exnessSessionCloseHour', 22),
            'adaptive_exit_enabled': bot.get('adaptiveExitEnabled', True),
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching Exness hold config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 📝 Integration Checklist

### Phase 1: Configuration & Persistence
- [ ] Add database columns for floor levels, hold times
- [ ] Update bot config defaults
- [ ] Add API endpoints for configuration

### Phase 2: Core Logic
- [ ] Implement `_map_binance_top_mover_symbol_to_broker()` for Exness
- [ ] Implement floor trading validation
- [ ] Implement signal identification
- [ ] Implement hold period calculation

### Phase 3: Trading Loop Integration
- [ ] Check floor before entry
- [ ] Update floor after close
- [ ] Identify trade origin (signal vs scanner)
- [ ] Apply signal-specific protection
- [ ] Use broker-specific hold times

### Phase 4: Testing & Monitoring
- [ ] Test top movers on demo Exness account
- [ ] Test floor guard blocking trades
- [ ] Test signal protection active
- [ ] Test extended holds working
- [ ] Monitor logs for each feature

---

## 🔧 Testing Checklist

```bash
# Test 1: Top Movers
curl -X GET http://localhost:5000/api/bot/BOT_ID/top-movers \
  -H "Authorization: Bearer SESSION_TOKEN"

# Test 2: Floor Config
curl -X PUT http://localhost:5000/api/bot/BOT_ID/floor-config \
  -H "Content-Type: application/json" \
  -d '{
    "floorTradingEnabled": true,
    "floorLevels": {"EURUSD": 1.0850},
    "floorUpdateStrategy": "profit_close"
  }'

# Test 3: Signal Protection
curl -X PUT http://localhost:5000/api/bot/BOT_ID/signal-protection \
  -H "Content-Type: application/json" \
  -d '{
    "signalProfitPreservationEnabled": true,
    "signalProtectionProfile": "strict"
  }'

# Test 4: Exness Hold Times
curl -X GET http://localhost:5000/api/bot/BOT_ID/exness-hold-config \
  -H "Authorization: Bearer SESSION_TOKEN"
```

---

## 📊 Expected Outcomes

| Feature | Before | After |
|---------|--------|-------|
| **Top Movers** | Manual symbol selection | Auto-discovered momentum trades |
| **Floor Trading** | All prices traded | Below-floor entries blocked |
| **Signal Profit** | Same protection for all trades | Stricter rules for signals |
| **Exness Hold** | 20-45 min holds | 45-120 min adaptive holds |

---

## ⚠️ Production Considerations

1. **Database**: Backup before adding new columns
2. **Rollback**: Keep previous version runnable
3. **Staging**: Test on demo accounts first
4. **Monitoring**: Add logs for each feature
5. **Gradual Rollout**: Enable features per user first

---

## 📚 Related Documentation

- `profit_peak_protection_solution.md` - Existing profit protection
- `zwesta_backend_notes.md` - Backend configuration notes
- Binance API: https://binance-docs.github.io/apidocs/
- Exness MT5 Documentation

---

**Last Updated**: 2026-08-13  
**Next Review**: After implementation complete  
**Owner**: Zwesta Trading Backend Team
