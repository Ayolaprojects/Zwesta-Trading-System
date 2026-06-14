"""
Binance Symbol Signal Tester
============================
Tests signal strength for a wide list of Binance USDT pairs using the same
RSI / MACD / trend logic as the backend scanner.

Run:  python test_binance_signals.py
      python test_binance_signals.py --threshold 50   (only show >= 50 strength)
      python test_binance_signals.py --interval 15m   (change kline interval)
      python test_binance_signals.py --add DOGEUSDT XRPUSDT   (add extra symbols)
"""

import urllib.request
import json
import time
import sys
import argparse
from datetime import datetime

# ─── CONFIG ─────────────────────────────────────────────────────────────────
BINANCE_BASE = "https://api.binance.com"

# All symbols to test (can be extended via --add flag)
DEFAULT_SYMBOLS = [
    # Majors (kept for reference)
    "BTCUSDT", "ETHUSDT",
    # Large caps
    "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT",
    "AVAXUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "MATICUSDT",
    "UNIUSDT", "ATOMUSDT", "TRXUSDT", "NEARUSDT", "XLMUSDT",
    # Mid caps
    "AAVEUSDT", "FTMUSDT", "SANDUSDT", "MANAUSDT", "GALAUSDT",
    "CHZUSDT", "ENJUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT",
    "1000XECEUSDT", "SUIUSDT", "APTUSDT", "ARBUSDT", "OPUSDT",
    "INJUSDT", "SEIUSDT", "TIAUSDT", "ONDOUSDT", "RENDERUSDT",
    # BTC pairs
    "ETHBTC", "BNBBTC", "SOLBTC", "XRPBTC",
    # BNB pairs
    "ETHBNB", "SOLBNB",
]

# ─── INDICATOR FUNCTIONS (identical to backend) ──────────────────────────────

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50
    rs = avg_gain / avg_loss
    return min(100, max(0, 100 - (100 / (1 + rs))))


def calculate_macd(prices, fast=12, slow=26, signal=9):
    def _ema(data, period):
        if len(data) < period:
            return data[-1] if data else 0.0
        alpha = 2.0 / (period + 1)
        ema_val = sum(data[:period]) / period
        for price in data[period:]:
            ema_val = alpha * price + (1.0 - alpha) * ema_val
        return ema_val

    min_len = slow + signal
    if len(prices) < min_len:
        return 0.0, 0.0, 0.0

    macd_series = []
    for offset in range(signal, 0, -1):
        sub = prices[:-offset]
        if len(sub) >= slow:
            macd_series.append(_ema(sub, fast) - _ema(sub, slow))
    macd_line = _ema(prices, fast) - _ema(prices, slow)
    macd_series.append(macd_line)
    signal_line = _ema(macd_series, min(signal, len(macd_series)))
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_moving_averages(prices, short=10, long=20):
    if len(prices) < long:
        v = prices[-1] if prices else 0
        return v, v
    return sum(prices[-short:]) / short, sum(prices[-long:]) / long


def evaluate_signal(symbol, closes, volatility_pct=1.0):
    """Same logic as backend evaluate_real_trade_signal (simplified, no broker params)"""
    price_history = closes[-50:]
    current_price = price_history[-1]

    rsi = calculate_rsi(price_history, 14)
    ma_short, ma_long = calculate_moving_averages(price_history, 10, 20)
    macd_line, signal_line, histogram = calculate_macd(price_history)

    # Trend
    ma_diff_pct = (current_price - ma_long) / ma_long * 100 if ma_long > 0 else 0
    if ma_diff_pct > 0.15:
        trend = 'UP' if ma_short > ma_long else 'RANGING'
    elif ma_diff_pct < -0.15:
        trend = 'DOWN'
    else:
        if ma_short > ma_long:
            trend = 'UP'
        elif ma_short < ma_long:
            trend = 'DOWN'
        else:
            trend = 'RANGING'

    # Volatility
    vol_high, vol_low = 2.0, 0.5
    if volatility_pct > vol_high:
        volatility = 'HIGH'
    elif volatility_pct > vol_low:
        volatility = 'MEDIUM'
    else:
        volatility = 'LOW'

    # MACD direction
    macd_prev_histogram = 0.0
    if len(price_history) >= 36:
        _, _, macd_prev_histogram = calculate_macd(price_history[:-1])
    macd_just_crossed_bullish = histogram > 0 and macd_prev_histogram <= 0
    macd_just_crossed_bearish = histogram < 0 and macd_prev_histogram >= 0
    if histogram > 0 and macd_line > signal_line:
        macd_signal = 'BUY'
    elif histogram < 0 and macd_line < signal_line:
        macd_signal = 'SELL'
    else:
        macd_signal = 'NEUTRAL'

    trend_gap_pct = abs(ma_short - ma_long) / ma_long * 100 if ma_long > 0 else 0
    strong_trend = trend_gap_pct >= 0.18

    # RSI scoring
    strength = 0
    signal = 'NEUTRAL'
    reasons = []

    if rsi < 33:
        signal, rsi_strength = 'BUY', 35
        reasons.append(f'RSI deeply oversold ({rsi:.0f})')
    elif rsi < 42:
        signal, rsi_strength = 'BUY', 25
        reasons.append(f'RSI oversold ({rsi:.0f})')
    elif rsi < 52 and macd_signal == 'BUY' and (trend == 'UP' or macd_just_crossed_bullish):
        signal, rsi_strength = 'BUY', 20
        reasons.append(f'RSI neutral ({rsi:.0f}) + uptrend/MACD crossover')
    elif rsi > 67:
        signal, rsi_strength = 'SELL', 35
        reasons.append(f'RSI deeply overbought ({rsi:.0f})')
    elif rsi > 60:
        signal, rsi_strength = 'SELL', 25
        reasons.append(f'RSI overbought ({rsi:.0f})')
    elif rsi > 50 and macd_signal == 'SELL' and (trend == 'DOWN' or macd_just_crossed_bearish):
        signal, rsi_strength = 'SELL', 20
        reasons.append(f'RSI neutral ({rsi:.0f}) + downtrend/MACD crossover')
    else:
        if macd_signal == 'BUY' and (trend == 'UP' or macd_just_crossed_bullish):
            signal, rsi_strength = 'BUY', 15
            reasons.append(f'RSI neutral ({rsi:.0f}) + trend/MACD confirmation')
        elif macd_signal == 'SELL' and (trend == 'DOWN' or macd_just_crossed_bearish):
            signal, rsi_strength = 'SELL', 15
            reasons.append(f'RSI neutral ({rsi:.0f}) + trend/MACD confirmation')
        else:
            fallback_buy = macd_signal == 'BUY' and macd_just_crossed_bullish and 35 <= rsi <= 62
            fallback_sell = macd_signal == 'SELL' and macd_just_crossed_bearish and 38 <= rsi <= 65
            if fallback_buy or fallback_sell:
                signal = 'BUY' if fallback_buy else 'SELL'
                rsi_strength = 8
                reasons.append(f'RSI neutral ({rsi:.0f}) + fresh MACD crossover')
            else:
                rsi_strength = 0
                reasons.append(f'RSI neutral ({rsi:.0f})')

    strength += rsi_strength
    extreme_reversal = signal != 'NEUTRAL' and rsi_strength >= 35 and volatility in {'LOW', 'MEDIUM'}

    # MACD confirmation
    if signal != 'NEUTRAL':
        if macd_signal == signal:
            strength += 25
            reasons.append(f'MACD confirms {signal}')
            if (signal == 'BUY' and macd_just_crossed_bullish) or (signal == 'SELL' and macd_just_crossed_bearish):
                strength += 15
                reasons.append('MACD crossover detected')
        else:
            penalty = 5 if extreme_reversal else 15
            strength -= penalty
            if strength < 0:
                signal = 'NEUTRAL'

    # Trend bonus
    if signal != 'NEUTRAL':
        if (signal == 'BUY' and trend == 'UP') or (signal == 'SELL' and trend == 'DOWN'):
            strength += 15
            reasons.append(f'Trend {trend} confirms')
        elif trend == 'RANGING':
            strength -= 20
            if strength < 35:
                signal = 'NEUTRAL'

    # Volatility adjustments
    if volatility == 'HIGH':
        strength -= 15
        if strength < 40:
            signal = 'NEUTRAL'
    elif volatility == 'LOW':
        strength += 10

    # Confirmation stacking
    if signal != 'NEUTRAL':
        cc = 0
        if rsi_strength >= 20: cc += 1
        if macd_signal == signal: cc += 1
        if (signal == 'BUY' and trend == 'UP') or (signal == 'SELL' and trend == 'DOWN'): cc += 1
        if strong_trend: cc += 1
        if volatility == 'LOW': cc += 1

        if strong_trend:
            tb = 8 if trend_gap_pct >= 0.35 else 4
            strength += tb
        if abs(ma_diff_pct) >= 0.35:
            strength += 4

        if cc >= 4:
            strength = (strength * 1.18) + 6
        elif cc == 3:
            strength = (strength * 1.10) + 4
        elif cc == 2 and strength >= 35:
            strength += 3

    strength = min(100, max(0, strength))

    if signal != 'NEUTRAL' and strength >= 70:
        signal = f'STRONG_{signal}'

    return {
        'signal': signal,
        'strength': round(strength, 1),
        'rsi': round(rsi, 1),
        'trend': trend,
        'volatility': volatility,
        'reason': ' | '.join(reasons) if reasons else 'Neutral',
    }


# ─── BINANCE DATA FETCH ──────────────────────────────────────────────────────

def fetch_klines(symbol, interval='5m', limit=100):
    """Fetch kline close prices from Binance public API"""
    url = f"{BINANCE_BASE}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            closes = [float(k[4]) for k in data]   # index 4 = close price
            highs  = [float(k[2]) for k in data]   # index 2 = high
            lows   = [float(k[3]) for k in data]   # index 3 = low
            return closes, highs, lows
    except Exception as e:
        return None, None, None


def calc_volatility_pct(closes, highs, lows, period=14):
    """Calculate average true range as % of price (proxy for volatility_pct)"""
    if not closes or len(closes) < 2:
        return 1.0
    trs = []
    for i in range(1, min(period + 1, len(closes))):
        high = highs[i]
        low = lows[i]
        prev_close = closes[i - 1]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    if not trs:
        return 1.0
    avg_tr = sum(trs) / len(trs)
    return (avg_tr / closes[-1]) * 100


def fetch_exchange_symbols():
    """Fetch all active USDT trading pairs from Binance"""
    url = f"{BINANCE_BASE}/api/v3/exchangeInfo"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return {
                s['symbol']
                for s in data['symbols']
                if s['status'] == 'TRADING' and s['quoteAsset'] in ('USDT', 'BTC', 'BNB')
            }
    except Exception as e:
        print(f"  [!] Could not fetch exchange info: {e}")
        return set()


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Binance Symbol Signal Tester")
    parser.add_argument('--threshold', type=float, default=0, help='Only show signals >= this strength (default: show all non-neutral)')
    parser.add_argument('--interval', default='5m', choices=['1m','3m','5m','15m','30m','1h','4h'], help='Kline interval (default: 5m)')
    parser.add_argument('--add', nargs='+', default=[], help='Extra symbols to test')
    parser.add_argument('--all-usdt', action='store_true', help='Test ALL USDT pairs on Binance (slow!)')
    parser.add_argument('--sort', default='strength', choices=['strength','rsi','symbol'], help='Sort results by')
    args = parser.parse_args()

    symbols = list(DEFAULT_SYMBOLS) + [s.upper() for s in args.add]

    if args.all_usdt:
        print("Fetching all active Binance USDT pairs...")
        valid = fetch_exchange_symbols()
        usdt_pairs = sorted([s for s in valid if s.endswith('USDT')])
        symbols = usdt_pairs
        print(f"  Found {len(usdt_pairs)} USDT pairs to test\n")

    print(f"{'='*80}")
    print(f"  Binance Signal Tester  |  Interval: {args.interval}  |  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Testing {len(symbols)} symbols | Threshold: {args.threshold}")
    print(f"{'='*80}")
    print(f"{'Symbol':<16} {'Signal':<16} {'Str':>5} {'RSI':>6} {'Trend':<9} {'Vol':<8}  Reason")
    print(f"{'-'*80}")

    results = []
    errors = []

    for i, symbol in enumerate(symbols):
        closes, highs, lows = fetch_klines(symbol, args.interval)
        if closes is None or len(closes) < 35:
            errors.append(symbol)
            continue

        vol_pct = calc_volatility_pct(closes, highs, lows)
        sig = evaluate_signal(symbol, closes, vol_pct)
        sig['symbol'] = symbol

        if sig['signal'] == 'NEUTRAL':
            continue
        if sig['strength'] < args.threshold:
            continue

        results.append(sig)

        # Rate-limit: ~10 req/sec is safe for Binance public API
        if i % 10 == 9:
            time.sleep(0.5)

    # Sort
    if args.sort == 'strength':
        results.sort(key=lambda x: x['strength'], reverse=True)
    elif args.sort == 'rsi':
        results.sort(key=lambda x: x['rsi'])
    else:
        results.sort(key=lambda x: x['symbol'])

    for r in results:
        sig_display = r['signal']
        # Color coding via ANSI (works in most terminals)
        if 'STRONG_BUY' in sig_display:
            sig_colored = f"\033[92m{sig_display:<16}\033[0m"
        elif 'BUY' in sig_display:
            sig_colored = f"\033[32m{sig_display:<16}\033[0m"
        elif 'STRONG_SELL' in sig_display:
            sig_colored = f"\033[91m{sig_display:<16}\033[0m"
        elif 'SELL' in sig_display:
            sig_colored = f"\033[31m{sig_display:<16}\033[0m"
        else:
            sig_colored = f"{sig_display:<16}"

        reason_short = r['reason'][:50]
        print(f"{r['symbol']:<16} {sig_colored} {r['strength']:>5.1f} {r['rsi']:>6.1f} {r['trend']:<9} {r['volatility']:<8}  {reason_short}")

    print(f"\n{'='*80}")
    print(f"  Results: {len(results)} tradable signals found out of {len(symbols) - len(errors)} tested")
    if errors:
        print(f"  Skipped (no data): {', '.join(errors[:10])}{'...' if len(errors)>10 else ''}")

    # ─── SCANNER RECOMMENDATION ─────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  SCANNER THRESHOLD RECOMMENDATION")
    print(f"{'='*80}")

    if results:
        strong = [r for r in results if r['strength'] >= 70]
        medium = [r for r in results if 50 <= r['strength'] < 70]
        weak   = [r for r in results if r['strength'] < 50]

        print(f"  STRONG signals (>=70): {len(strong)} symbols")
        for r in strong[:10]:
            print(f"    * {r['symbol']:<16} {r['signal']:<18} strength={r['strength']:.1f}")

        print(f"\n  MEDIUM signals (50-69): {len(medium)} symbols")
        for r in medium[:10]:
            print(f"    * {r['symbol']:<16} {r['signal']:<18} strength={r['strength']:.1f}")

        if weak:
            print(f"\n  WEAK signals (<50): {len(weak)} symbols (not recommended for scanner)")

        # Recommend threshold
        if strong:
            rec_symbols = [r['symbol'] for r in strong[:8]]
            print(f"\n  RECOMMENDED SCANNER SYMBOLS:  {', '.join(rec_symbols)}")
            print(f"  RECOMMENDED SIGNAL THRESHOLD: 60-65")
            print(f"    (Set binanceAltSignalThresholdDiscount=8 to give alts an 8pt lower bar)")
        elif medium:
            rec_symbols = [r['symbol'] for r in medium[:8]]
            print(f"\n  RECOMMENDED SCANNER SYMBOLS:  {', '.join(rec_symbols)}")
            print(f"  RECOMMENDED SIGNAL THRESHOLD: 50-55")
        else:
            print("\n  No symbols currently meet recommended threshold. Market may be ranging.")
            print("  Try a lower threshold (--threshold 30) or different interval (--interval 15m)")
    else:
        print("  No non-neutral signals found. Market is flat right now.")
        print("  Suggestions:")
        print("    • Try --interval 15m or --interval 1h for longer timeframe signals")
        print("    • Try --threshold 0 to show all non-neutral signals")

    print(f"\n  Run again to refresh:  python test_binance_signals.py --interval {args.interval}")
    print(f"  Test all USDT pairs:   python test_binance_signals.py --all-usdt")
    print(f"  Add custom symbols:    python test_binance_signals.py --add PEPEUSDT WIFUSDT")
    print()


if __name__ == '__main__':
    main()
