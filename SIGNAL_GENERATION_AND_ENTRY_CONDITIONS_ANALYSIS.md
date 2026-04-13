# Zwesta Trading Backend - Signal Generation & Entry Conditions Analysis

## Summary
This document extracts and explains the signal generation logic, entry conditions, volatility detection, and trade triggering mechanisms from the `multi_broker_backend_updated.py` file.

---

## 1. SIGNAL GENERATION LOGIC

### Core Function: `evaluate_real_trade_signal()` (Lines 9320-9550)

This is the CENTRAL SIGNAL EVALUATION FUNCTION that generates trading signals based on technical indicators.

**Location:** Line 9320

**Returns:**
```python
{
    'signal': 'STRONG_BUY' | 'BUY' | 'SELL' | 'STRONG_SELL' | 'NEUTRAL',
    'strength': 0-100,          # Signal confidence percentage
    'rsi': <float>,             # RSI value (0-100)
    'trend': 'UP' | 'DOWN' | 'RANGING',
    'volatility': 'HIGH' | 'MEDIUM' | 'LOW',
    'entry_reason': <string>,   # Explanation of why signal was generated
}
```

**Key Filters for High Win Rate:**
1. **Only BUY when RSI < 35** (not 45) and MACD confirms
2. **Only SELL when RSI > 65** (not 55) and MACD confirms
3. **Require MACD crossover + RSI extreme + Trend alignment**
4. **Skip RANGING markets entirely** (lowest probability trades)
5. **Higher signal threshold reduces false entries**

**Signal Generation Process:**

#### Step 1: Calculate Technical Indicators
- **RSI** (Line 9376): Relative Strength Index with period=14
- **Moving Averages** (Line 9377): 10-period (short) and 20-period (long)
- **MACD** (Line 9378): MACD line, signal line, and histogram

#### Step 2: Determine Trend (Lines 9390-9408)
```
IF price > MA20 + 0.15% → Uptrend (UP)
IF price < MA20 - 0.15% → Downtrend (DOWN)
ELSE → Consolidation (RANGING)
```

#### Step 3: Reject RANGING Markets (Lines 9414-9423)
Ranging markets have worst win rate, so they are rejected immediately with:
- `strength = 10`
- `signal = 'NEUTRAL'`
- `entry_reason = 'Skipping RANGING market - low probability'`

#### Step 4: RSI-Based Entry Conditions (Lines 9442-9481)

**STRONG OVERSOLD (BUY):**
- RSI < 28: Buy signal with strength=35
- Entry reason: "RSI deeply oversold ({RSI})"

**MODERATE OVERSOLD (BUY):**
- RSI 28-35: Buy signal with strength=25
- Entry reason: "RSI oversold ({RSI})"

**STRONG OVERBOUGHT (SELL):**
- RSI > 72: Sell signal with strength=35
- Entry reason: "RSI deeply overbought ({RSI})"

**MODERATE OVERBOUGHT (SELL):**
- RSI 65-72: Sell signal with strength=25
- Entry reason: "RSI overbought ({RSI})"

**PULLBACK IN UPTREND:**
- RSI 40-45 + Trend=UP + MACD=BUY + Strong trend
- Buy signal with strength=20
- Entry reason: "RSI neutral ({RSI}) + strong uptrend + MACD"

**PULLBACK IN DOWNTREND:**
- RSI 55-60 + Trend=DOWN + MACD=SELL + Strong trend
- Sell signal with strength=20
- Entry reason: "RSI neutral ({RSI}) + strong downtrend + MACD"

#### Step 5: MACD Confirmation (Lines 9483-9500)
If RSI signal is generated:
- **Confirms signal:** +25 strength, add "MACD confirms {SIGNAL}"
  - Fresh crossover bonus: +15 strength, add "MACD crossover detected"
- **Conflicts with signal:** -15 strength, may drop to NEUTRAL

#### Step 6: Trend Confirmation (Lines 9502-9508)
- **Signal aligned with trend:** +15 strength, add "Trend {TREND} confirms signal"
- **Signal opposes trend or RANGING:** -20 strength

#### Step 7: Volatility Adjustment (Lines 9510-9517)
- **HIGH volatility:** -15 strength, add "High volatility - reduced confidence"
  - If strength drops below 40: signal = NEUTRAL
- **LOW volatility:** +10 strength, add "Low volatility - favorable conditions"

#### Step 8: Final Signal Classification (Lines 9521-9527)
```python
IF signal != 'NEUTRAL':
    IF strength >= 70:
        signal = 'STRONG_{signal}'  # STRONG_BUY or STRONG_SELL
    ADD "Confidence: {strength}%"
```

---

## 2. RSI CALCULATION (Lines 9210-9239)

**Function:** `calculate_rsi(prices, period=14)`

```python
def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (RSI)
    
    RSI > 70 = Overbought (SELL signal)
    RSI < 30 = Oversold (BUY signal)
    RSI 30-70 = Neutral
    """
    Calculate price changes (deltas)
    Separate into gains and losses
    Average gain = sum(gains[-14:]) / 14
    Average loss = sum(losses[-14:]) / 14
    RS = avg_gain / avg_loss
    RSI = 100 - (100 / (1 + RS))
    Return RSI (0-100)
```

**Entry Conditions Based on RSI:**
- **< 28:** Strong BUY signal (deeply oversold)
- **28-35:** Moderate BUY (oversold)
- **35-42:** BUY (if trend confirms)
- **45-55:** Neutral - requires trend/MACD confirmation
- **55-65:** SELL (if trend confirms)
- **65-72:** Moderate SELL (overbought)
- **> 72:** Strong SELL signal (deeply overbought)

---

## 3. MOVING AVERAGES (Lines 9280-9295)

**Function:** `calculate_moving_averages(prices, short=10, long=20)`

Returns: `(sma_short, sma_long)`

**Entry Conditions:**
- **Price > MA20 & MA10 > MA20:** Strong uptrend → BUY opportunities
- **Price < MA20 & MA10 < MA20:** Strong downtrend → SELL opportunities
- **Price near MA20 (±0.15%):** Consolidation (RANGING) → Skip trading

---

## 4. MACD CALCULATION (Lines 9240-9279)

**Function:** `calculate_macd(prices, fast=12, slow=26, signal=9)`

Returns: `(macd_line, signal_line, histogram)`

**Entry Conditions:**
- **MACD > Signal & Histogram > 0:** Bullish (BUY signal)
- **MACD < Signal & Histogram < 0:** Bearish (SELL signal)
- **Histogram crosses above 0:** Fresh bullish crossover (BUY confirmation)
- **Histogram crosses below 0:** Fresh bearish crossover (SELL confirmation)

**Used for:**
- Confirming RSI signals
- Detecting momentum shifts
- Fresh crossover bonus (+15 strength)

---

## 5. VOLATILITY DETECTION (Lines 9298-9313)

**Function:** `calculate_atr(highs, lows, closes, period=14)`

Returns: Average True Range (ATR) for volatility measurement

**Volatility Classification (by Symbol):**

**Forex Pairs (Low Volatility):**
- EURUSD: 0.02 (low) - 0.18 (high)
- GBPUSD: 0.03 (low) - 0.20 (high)
- USDJPY: 0.04 (low) - 0.20 (high)

**Precious Metals (High Volatility):**
- XAUUSD (Gold): 0.05 (low) - 0.25 (high)
- XAGUSD (Silver): 0.08 (low) - 0.35 (high)

**Crypto (Very High Volatility):**
- BTCUSD: 0.30 (low) - 1.50 (high)
- ETHUSD: 0.40 (low) - 2.00 (high)

**Entry Conditions:**
- **HIGH volatility:** -15 strength (risky, fewer trades)
- **MEDIUM volatility:** 0 strength adjustment (normal conditions)
- **LOW volatility:** +10 strength (favorable, more reliable signals)

---

## 6. STRATEGY FUNCTIONS (Lines 9564-9828)

Seven core trading strategies use the signal evaluation to generate entry conditions:

### 6.1 Scalping Strategy (Lines 9564-9599)

**Entry Conditions:**
- Signal strength >= `min_signal_strength`
- Quick trades with small profits (2-3 pips)
- Best for: Liquid pairs (EURUSD), low volatility
- Volume: 0.7-1.0 lots (scaled by signal strength)
- Stop loss: 0.5× normal (tight for scalping)
- Take profit: 0.3× normal (quick exits)
- Duration: 5 minutes

### 6.2 Momentum Strategy (Lines 9599-9640)

**Entry Conditions:**
- Signal strength >= `min_signal_strength + 5` (stronger requirement)
- Trend != 'RANGING' (only trending markets)
- Signal direction matches trend (BUY in uptrend, SELL in downtrend)
- Volume: 1.5× signal_strength / 80 (scales with momentum)
- Take profit: 1.5× normal (bigger moves expected)
- Duration: 15 minutes

### 6.3 Trend Following Strategy (Lines 9637-9681)

**Entry Conditions:**
- Signal strength >= `min_signal_strength`
- Signal direction aligns with trend (no counter-trend trades)
- Volume: 0.9 lots (consistent sizing)
- Stop loss: 1.3× normal (wider for trend holds)
- Take profit: 2.0× normal (large trend targets)
- Duration: 1 hour

### 6.4 Mean Reversion Strategy (Lines 9673-9715)

**Entry Conditions:**
- **RSI < 30 OR RSI > 70** (extreme condition required)
- Signal strength >= `min_signal_strength - 5`
- Trade AGAINST extreme: SELL if RSI >70 (buy low), BUY if RSI <30 (sell high)
- Best for: Ranging markets, overbought/oversold conditions
- Volume: 1.1 lots
- Duration: 10 minutes

### 6.5 Range Trading Strategy (Lines 9708-9754)

**Entry Conditions:**
- Trend == 'RANGING' (must be consolidating)
- Signal strength >= `min_signal_strength - 10`
- Buy near support, Sell near resistance
- Volume: 1.3 lots (capitalize on range)
- Stop loss: 0.7× normal (tight for range)
- Take profit: 0.7× normal (quick exits when range breaks)
- Duration: 8 minutes

### 6.6 Breakout Strategy (Lines 9744-9795)

**Entry Conditions:**
- Signal strength >= `min_signal_strength + 10` (strong breakout required)
- Trend != 'RANGING' (price breaking out of consolidation)
- Signal direction matches trend
- Volume: 1.0 lots
- Stop loss: 1.2× normal (behind breakout level)
- Take profit: 2.5× normal (large continuation targets)
- Duration: 20 minutes

### 6.7 Swing Trend DCA Strategy (Lines 9780-9838)

**Entry Conditions (BEST FOR SMALL ACCOUNTS $10-$1000):**
- Trend != 'RANGING' (clear trend required)
- Signal strength >= max(min_strength + 10, 60) (very high bar)
- RSI confirmation required:
  - In UPTREND: RSI must be > 40 (not too deep pullback)
  - In DOWNTREND: RSI must be < 60 (not too shallow pullback)
- Volume: 0.01 lots (minimum to preserve capital)
- Stop loss: 1.5× normal (wide for swing holds)
- Take profit: 2.5× normal (large swing targets)
- Duration: 4 hours

---

## 7. ENTRY TRIGGER LOGIC (Line 12268)

**Function:** `execute_bot_trade(bot_id)` [NESTED in continuous_bot_trading_loop]

**How Trades Are Triggered:**

1. **Get bot configuration** (strategy, symbols, risk settings)
2. **For each symbol in bot's symbol list:**
   - Get market data (price history, current price)
   - Call `evaluate_real_trade_signal()` → Get signal evaluation
   - Extract signal direction: `'BUY'` or `'SELL'` from signal
   - Check signal strength >= `signalThreshold` (default: 50)
   - **IF signal passes threshold: Execute trade**

**Place Order:**
- Call `place_order(symbol, order_type, volume, stop_loss, take_profit)`
- MT5 connection places order with entry signal metadata

**Record Trade:**
- Insert into `trades` table with:
  - bot_id, user_id, symbol
  - Entry reason (from signal evaluation)
  - Signal strength
  - Order type (BUY/SELL)
  - P&L tracking

---

## 8. ADAPTIVE STRATEGY SELECTION (Lines 10018-10148)

**Function:** `_choose_strategy_for_cycle()`

**Strategy Selection Logic:**

1. **Check if strategy switch is allowed** (cooldown: 20 minutes)
2. **Scan all symbols** for opportunities with each strategy
3. **Calculate performance metrics** for recent trades
4. **Score each strategy:**
   - Win rate bonus
   - Profit factor weight
   - Stickiness bonus (prefer current strategy +4.0 multiplier)
5. **Select highest-scoring strategy**
6. **Update bot config** if strategy changed
7. **Log strategy switch** in strategyHistory

---

## 9. INTELLIGENT SCANNER (Lines 10390-10763)

**Function:** `scan_all_opportunities(strategy_func, account_id, risk_per_trade)`

**Scanner Operation:**

1. **Build symbol universe** from configured symbols
2. **For each symbol:**
   - Evaluate signal with current strategy function
   - Cache strategy parameters for efficiency
3. **Rank opportunities** by signal strength:
   - STRONG_BUY/STRONG_SELL: highest priority
   - BUY/SELL: medium priority
   - Top N opportunities are returned
4. **Fallback mechanism:**
   - If no opportunities found, retry with lower threshold
   - Use related symbols from same asset family (EUR*, GBP*, USD*)

---

## 10. VOLATILITY-BASED ENTRY CONDITIONS

Located in strategy profile sections (Lines 5969-9064):

**Symbol Parameter Structure:**
```python
SYMBOL_PARAMETERS = {
    'EURUSD': {
        'min_signal_strength': 50,
        'volatility_high': 0.18,
        'volatility_low': 0.02,
        'stop_loss_pips': 30,
        'take_profit_pips': 60,
    },
    'XAUUSD': {
        'min_signal_strength': 50,
        'volatility_high': 0.25,
        'volatility_low': 0.05,
        'stop_loss_pips': 50,
        'take_profit_pips': 100,
    },
    'BTCUSD': {
        'min_signal_strength': 50,
        'volatility_high': 1.5,
        'volatility_low': 0.3,
        'stop_loss_pips': 200,
        'take_profit_pips': 400,
    },
    # ... more symbols
}
```

**Default Parameters:**
```python
DEFAULT_SYMBOL_PARAMS = {
    'min_signal_strength': 50,       # Minimum signal strength to trade (0-100)
    'volatility_high': 0.15,         # High volatility threshold
    'volatility_low': 0.02,          # Low volatility threshold
    'stop_loss_pips': 30,            # Stop loss distance
    'take_profit_pips': 60,          # Take profit distance
}
```

---

## 11. SIGNAL STRENGTH CALCULATION SUMMARY

**Starting Strength: 0**

| Event | Change | Conditions |
|-------|--------|-----------|
| RSI < 28 (Deep Oversold) | +35 | BUY signal |
| RSI 28-35 (Oversold) | +25 | BUY signal |
| RSI 40-45 + Uptrend + MACD | +20 | Pullback BUY |
| RSI > 72 (Deep Overbought) | +35 | SELL signal |
| RSI 65-72 (Overbought) | +25 | SELL signal |
| RSI 55-60 + Downtrend + MACD | +20 | Pullback SELL |
| MACD Confirms Signal | +25 | +15 if fresh crossover |
| MACD Conflicts | -15 | Weakens or kills signal |
| Trend Aligns (UP→BUY, DOWN→SELL) | +15 | Confirmation |
| Trend Opposes or RANGING | -20 | Contradiction |
| High Volatility | -15 | Risk penalty |
| Low Volatility | +10 | Risk bonus |
| **Final:** Strength >= 70 | 🔴 STRONG_BUY/SELL | Trade executed |
| **Final:** 50-70 Strength | 🟡 BUY/SELL | Trade executed (if above threshold) |
| **Final:** < 50 Strength | 🟢 NEUTRAL | No trade |

---

## 12. PEAK AND UPSWING DETECTION

**Method:** Embedded in trend calculation (Lines 9390-9408)

- **PEAK:** When RSI reaches > 70 in consolidation → SELL signal
- **UPSWING:** When RSI rises from < 30 + MACD > Signal → BUY signal
- **Continuation:** Monitored by MACD histogram staying positive (BUY) or nagative (SELL)

---

## 13. KEY ENTRY SIGNAL DETERMINATIONS

**Where Entry Signal Logic Determines When to Trigger Trade:**

1. **Signal Threshold Check** (Line 16109):
   ```python
   current_threshold = max(int(bot_config.get('signalThreshold') or 50), 30)
   IF signal_strength >= current_threshold: EXECUTE_TRADE
   ```

2. **Strategy Filter Check** (Lines 9564-9838):
   Each strategy returns `{...trade_params...}` if entry conditions met, else `None`

3. **Risk Management Check** (Line 12526):
   ```python
   def should_trade_symbol_based_on_risk_management(bot_config, symbol):
       Check daily loss limit, position size, margin availability
   ```

4. **Market Hours Check** (Line 12330):
   ```python
   def should_trade_today(bot_config, symbol):
       Check if symbol market is open
   ```

5. **Execution** (Line 12268):
   ```python
   def execute_bot_trade(bot_id):
       IF all checks pass: place_order(symbol, order_type, volume, ...)
   ```

---

## 14. ADAPTIVE THRESHOLDS (Lines 16232-16362)

**Automatic Signal Threshold Adjustment:**

```python
def update_adaptive_signal_threshold_state(bot_config):
    # IF recent win rate < 45%: INCREASE threshold to 60+ (fewer trades)
    # IF recent win rate > 55%: DECREASE threshold to 40+ (more trades)
    # Prevents overtrading in low-probability periods
    # Max adjustment offset: 20 points from base
```

---

## SUMMARY OF ENTRY SIGNALS

| Signal | Condition | Strength | Trade Action |
|--------|-----------|----------|--------------|
| **STRONG_BUY** | RSI<28 + MACD>Signal + Trend=UP + strength≥70 | 70-100 | 🟢 EXECUTE |
| **BUY** | RSI<35 + MACD>Signal + strength≥50 | 50-69 | 🟢 EXECUTE |
| **BUY (Pullback)** | Uptrend + RSI 40-45 + MACD + strength≥50 | 50-69 | 🟢 EXECUTE |
| **STRONG_SELL** | RSI>72 + MACD<Signal + Trend=DOWN + strength≥70 | 70-100 | 🟢 EXECUTE |
| **SELL** | RSI>65 + MACD<Signal + strength≥50 | 50-69 | 🟢 EXECUTE |
| **SELL (Pullback)** | Downtrend + RSI 55-60 + MACD + strength≥50 | 50-69 | 🟢 EXECUTE |
| **NEUTRAL** | RSI 45-55 without confirmation / RANGING market / strength<50 | <50 | ❌ SKIP |

---

## FILES AND LINE REFERENCES

| Component | File | Lines | Function |
|-----------|------|-------|----------|
| Signal Evaluation | multi_broker_backend_updated.py | 9320-9550 | `evaluate_real_trade_signal()` |
| RSI Calculation | multi_broker_backend_updated.py | 9210-9239 | `calculate_rsi()` |
| MACD Calculation | multi_broker_backend_updated.py | 9240-9279 | `calculate_macd()` |
| Moving Averages | multi_broker_backend_updated.py | 9280-9295 | `calculate_moving_averages()` |
| ATR/Volatility | multi_broker_backend_updated.py | 9296-9313 | `calculate_atr()` |
| Scalping Strategy | multi_broker_backend_updated.py | 9564-9599 | `scalping_strategy()` |
| Momentum Strategy | multi_broker_backend_updated.py | 9599-9640 | `momentum_strategy()` |
| Trend Following | multi_broker_backend_updated.py | 9637-9681 | `trend_following_strategy()` |
| Mean Reversion | multi_broker_backend_updated.py | 9673-9715 | `mean_reversion_strategy()` |
| Range Trading | multi_broker_backend_updated.py | 9708-9754 | `range_trading_strategy()` |
| Breakout Strategy | multi_broker_backend_updated.py | 9744-9795 | `breakout_strategy()` |
| Swing Trend DCA | multi_broker_backend_updated.py | 9780-9838 | `swing_trend_dca_strategy()` |
| Signal Direction | multi_broker_backend_updated.py | 9830-9836 | `extract_signal_direction()` |
| Strategy Selection | multi_broker_backend_updated.py | 10018-10148 | `_choose_strategy_for_cycle()` |
| Opportunity Scanner | multi_broker_backend_updated.py | 10390-10763 | `scan_all_opportunities()` |
| Bot Trading Loop | multi_broker_backend_updated.py | 17196+ | `continuous_bot_trading_loop()` |
| Trade Execution | multi_broker_backend_updated.py | 12268 | `execute_bot_trade()` [nested] |
| Trade Placement | multi_broker_backend_updated.py | 2574-3850 | `MT5Connection.place_order()` |
| Symbol Parameters | multi_broker_backend_updated.py | 8900-9064 | `SYMBOL_PARAMETERS` dict |

---

**Document Generated:** 2026-04-13
**Backend Version:** 2.0.0+
**Last Updated:** 2025-03-25
