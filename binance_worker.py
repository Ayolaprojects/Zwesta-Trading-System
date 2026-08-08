#!/usr/bin/env python3
"""
Binance Worker Process - Zwesta Trading Platform
=================================================
Dedicated worker for Binance bot trading. Runs as a SEPARATE PROCESS
with no MT5 dependency. Designed for 500 concurrent Binance bot threads.

Architecture:
  Flask API  ──── worker_bot_queue (DB) ────► Binance Worker 1 (this file)
                                          ├──► Binance Worker 2
                                          └──► Binance Worker N

  Binance Market Data Service ──► Redis ────► Binance Worker (price reads)

Communication: SQLite/PostgreSQL via worker_bot_queue, worker_pool tables
Price data:    Redis (shared) → fallback Binance REST ticker
Trading:       Binance REST API (per-user API key/secret)

Capacity: 1 worker = 500 bot threads (I/O-bound, GIL not a bottleneck)
Deploy 5 workers = 2,500 concurrent bots = 5,000 users at 10% concurrency
"""

import os
import sys
import json
import time
import hmac
import uuid
import hashlib
import sqlite3
import signal
import logging
import threading
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import redis as redis_lib
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# ==================== CONFIGURATION ====================
DATABASE_PATH = os.environ.get('DATABASE_PATH', r'C:\backend\zwesta_trading.db')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
WORKER_INSTANCE_ID = int(os.environ.get('BINANCE_WORKER_ID', '1'))
MAX_BOTS_PER_WORKER = int(os.environ.get('MAX_BOTS_PER_BINANCE_WORKER', '500'))
HEARTBEAT_INTERVAL = 10          # seconds
COMMAND_POLL_INTERVAL = 2        # seconds
DEFAULT_TRADING_INTERVAL = 60   # 1 minute between trade cycles for faster profit capture
PRICE_CACHE_TTL = 15             # 15 seconds — fresher prices for faster signals
BINANCE_REQUEST_TIMEOUT = 10     # 10 seconds — faster failover

# ==================== PROFIT MAXIMIZATION SETTINGS ====================
DEFAULT_TAKE_PROFIT_PCT = 0.025   # 2.5% take-profit target
DEFAULT_STOP_LOSS_PCT = 0.012     # 1.2% stop-loss (1:2 risk-reward)
TRAILING_STOP_PCT = 0.010         # 1.0% trailing stop activation
TRAILING_STEP_PCT = 0.005         # 0.5% trailing step
COMPOUND_REINVEST_PCT = 0.5       # Reinvest 50% of realized profits
MAX_CONSECUTIVE_LOSSES = 3        # Auto-reduce lot size after 3 consecutive losses
LOT_SIZE_REDUCTION_FACTOR = 0.5   # Halve lot size after max consecutive losses
LOT_SIZE_RESTORE_AFTER = 5        # Restore lot size after 5 consecutive wins
MIN_LOT_SIZE_USDT = 5.0           # Minimum lot size
MAX_LOT_SIZE_USDT = 500.0         # Maximum lot size per trade

# Binance base URLs (overridable for region restrictions)
BINANCE_LIVE_URL = os.environ.get('BINANCE_REST_BASE', 'https://api.binance.com/api')
BINANCE_TEST_URL = os.environ.get('BINANCE_TEST_REST_BASE', 'https://testnet.binance.vision/api')

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format=f'%(asctime)s [BinanceWorker-{WORKER_INSTANCE_ID}] %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ==================== WORKER STATE ====================
worker_running = True
active_bots: Dict[str, Dict] = {}     # bot_id -> config
bot_threads: Dict[str, threading.Thread] = {}
bot_stop_flags: Dict[str, bool] = {}

# Redis client (shared price cache, optional)
_redis_client: Optional[object] = None
_redis_lock = threading.Lock()


# ==================== REDIS PRICE CACHE ====================

def get_redis_client():
    """Lazy-initialize Redis client. Returns None when Redis unavailable."""
    global _redis_client
    if not REDIS_AVAILABLE:
        return None
    with _redis_lock:
        if _redis_client is None:
            try:
                _redis_client = redis_lib.from_url(REDIS_URL, socket_timeout=2, socket_connect_timeout=2)
                _redis_client.ping()
                logger.info(f"Redis connected: {REDIS_URL}")
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}) — will use Binance REST for prices")
                _redis_client = False  # Sentinel to avoid retry spam
        return _redis_client if _redis_client else None


def get_cached_price(symbol: str) -> Optional[float]:
    """Read latest price from Redis cache (written by binance_market_data.py)."""
    try:
        r = get_redis_client()
        if not r:
            return None
        raw = r.get(f'binance:price:{symbol.upper()}')
        if raw is None:
            return None
        data = json.loads(raw)
        # Check freshness
        age = time.time() - float(data.get('ts', 0))
        if age > PRICE_CACHE_TTL:
            return None
        return float(data['price'])
    except Exception:
        return None


# ==================== BINANCE REST CLIENT ====================

class BinanceClient:
    """Lightweight per-user Binance REST client. No external dependencies beyond requests."""

    SYMBOL_MAP = {
        'BTCUSD': 'BTCUSDT', 'ETHUSD': 'ETHUSDT', 'BNBUSD': 'BNBUSDT',
        'SOLUSD': 'SOLUSDT', 'XRPUSD': 'XRPUSDT', 'ADAUSD': 'ADAUSDT',
        'DOGEUSD': 'DOGEUSDT', 'AVAXUSD': 'AVAXUSDT', 'MATICUSD': 'MATICUSDT',
        'LINKUSD': 'LINKUSDT', 'DOTUSD': 'DOTUSDT', 'LTCUSD': 'LTCUSDT',
    }
    QUOTE_ASSETS = ('USDT', 'USDC', 'FDUSD', 'TUSD', 'BTC', 'ETH', 'BNB', 'USD', 'EUR', 'GBP', 'TRY', 'BRL', 'ARS', 'AUD', 'JPY')

    def __init__(self, api_key: str, api_secret: str, is_live: bool = False):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.base_url = BINANCE_LIVE_URL if is_live else BINANCE_TEST_URL
        self._session = requests.Session()
        self._session.headers.update({'X-MBX-APIKEY': self.api_key})

    def normalize_symbol(self, symbol: str) -> Optional[str]:
        s = symbol.upper().replace('/', '').replace('_', '').replace('-', '')
        if s in self.SYMBOL_MAP:
            return self.SYMBOL_MAP[s]
        if any(s.endswith(quote) and len(s) > len(quote) for quote in self.QUOTE_ASSETS):
            return s
        return None

    def _sign(self, params: Dict) -> Dict:
        p = dict(params)
        p['timestamp'] = int(time.time() * 1000)
        p['recvWindow'] = 5000
        query = urlencode(p)
        sig = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        p['signature'] = sig
        return p

    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol via REST (fallback when Redis unavailable)."""
        try:
            norm = self.normalize_symbol(symbol)
            if not norm:
                return None
            resp = self._session.get(
                f'{self.base_url}/v3/ticker/price',
                params={'symbol': norm},
                timeout=BINANCE_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                return float(resp.json()['price'])
        except Exception as e:
            logger.debug(f"get_price({symbol}) failed: {e}")
        return None

    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 50) -> List[Dict]:
        """Fetch OHLCV candles. Returns list of {open,high,low,close,volume}."""
        try:
            norm = self.normalize_symbol(symbol)
            if not norm:
                return []
            resp = self._session.get(
                f'{self.base_url}/v3/klines',
                params={'symbol': norm, 'interval': interval, 'limit': limit},
                timeout=BINANCE_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                return [
                    {
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5]),
                        'time': k[0],
                    }
                    for k in resp.json()
                ]
        except Exception as e:
            logger.debug(f"get_klines({symbol}) failed: {e}")
        return []

    def get_account_balance(self) -> Optional[Dict]:
        """Get USDT balance from Binance account."""
        try:
            resp = self._session.get(
                f'{self.base_url}/v3/account',
                params=self._sign({}),
                timeout=BINANCE_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                balances = resp.json().get('balances', [])
                usdt = next((b for b in balances if b['asset'] == 'USDT'), None)
                if usdt:
                    return {
                        'free': float(usdt['free']),
                        'locked': float(usdt['locked']),
                        'total': float(usdt['free']) + float(usdt['locked']),
                    }
        except Exception as e:
            logger.debug(f"get_account_balance failed: {e}")
        return None

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """Place a market order. side='BUY' or 'SELL'."""
        try:
            norm = self.normalize_symbol(symbol)
            if not norm:
                return {'success': False, 'error': f'Unsupported symbol: {symbol}'}

            params = self._sign({
                'symbol': norm,
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': f'{quantity:.6f}'.rstrip('0').rstrip('.') or '0.001',
            })
            resp = self._session.post(
                f'{self.base_url}/v3/order',
                params=params,
                timeout=BINANCE_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    'success': True,
                    'orderId': str(data.get('orderId', '')),
                    'symbol': norm,
                    'side': side.upper(),
                    'quantity': quantity,
                    'status': data.get('status', 'FILLED'),
                    'fills': data.get('fills', []),
                }
            else:
                err = resp.json() if resp.text else {}
                return {
                    'success': False,
                    'error': err.get('msg', resp.text),
                    'code': err.get('code', resp.status_code),
                }
        except Exception as e:
            logger.error(f"place_market_order exception: {e}")
            return {'success': False, 'error': str(e)}

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol trading rules (min qty, step size, etc)."""
        try:
            norm = self.normalize_symbol(symbol)
            if not norm:
                return None
            resp = self._session.get(
                f'{self.base_url}/v3/exchangeInfo',
                params={'symbol': norm},
                timeout=BINANCE_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                symbols = resp.json().get('symbols', [])
                for s in symbols:
                    if s['symbol'] == norm:
                        return s
        except Exception:
            pass
        return None


# ==================== TECHNICAL INDICATORS ====================

def calculate_rsi(closes: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index (RSI)."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def calculate_ema(closes: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average."""
    if len(closes) < period:
        return None
    k = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return round(ema, 6)


def calculate_signal(
    symbol: str,
    strategy: str,
    klines: List[Dict],
    current_price: float,
    bot_config: Dict,
) -> Optional[str]:
    """
    Generate BUY/SELL/None signal based on strategy.

    Strategies:
    - RSI:      Buy RSI < 35 (oversold), Sell RSI > 65 (overbought) — wider bands
    - EMA:      Buy when price > EMA20, Sell when price < EMA20
    - MOMENTUM: Buy on 3 consecutive green candles, Sell on 3 red
    - SCALP:    Fast RSI(7) with tighter bands 30/70
    - AUTO:     RSI + EMA confirmation (more reliable)
    - TREND:    EMA crossover with momentum — rides trends longer
    """
    if not klines or len(klines) < 20:
        return None

    closes = [k['close'] for k in klines]
    strategy_upper = (strategy or 'AUTO').upper()

    if strategy_upper == 'RSI':
        rsi = calculate_rsi(closes, 14)
        if rsi is None:
            return None
        if rsi < 35:
            return 'BUY'
        if rsi > 65:
            return 'SELL'
        return None

    elif strategy_upper == 'EMA':
        ema20 = calculate_ema(closes, 20)
        ema50 = calculate_ema(closes, 50)
        if ema20 is None or ema50 is None:
            return None
        if current_price > ema20 and ema20 > ema50:
            return 'BUY'
        if current_price < ema20 and ema20 < ema50:
            return 'SELL'
        return None

    elif strategy_upper == 'MOMENTUM':
        if len(closes) < 4:
            return None
        last3 = closes[-3:]
        if last3[0] < last3[1] < last3[2]:  # 3 rising candles
            return 'BUY'
        if last3[0] > last3[1] > last3[2]:  # 3 falling candles
            return 'SELL'
        return None

    elif strategy_upper == 'SCALP':
        rsi = calculate_rsi(closes, 7)
        if rsi is None:
            return None
        if rsi < 30:
            return 'BUY'
        if rsi > 70:
            return 'SELL'
        return None

    elif strategy_upper == 'TREND':
        ema20 = calculate_ema(closes, 20)
        ema50 = calculate_ema(closes, 50)
        ema100 = calculate_ema(closes, 100)
        if ema20 is None or ema50 is None:
            return None
        # Strong trend: price above all EMAs and EMA20 > EMA50 > EMA100
        if current_price > ema20 and ema20 > ema50:
            if ema100 is None or ema50 > ema100:
                return 'BUY'
        # Strong downtrend: price below all EMAs and EMA20 < EMA50 < EMA100
        if current_price < ema20 and ema20 < ema50:
            if ema100 is None or ema50 < ema100:
                return 'SELL'
        return None

    else:  # AUTO: RSI + EMA confirmation — more aggressive thresholds
        rsi = calculate_rsi(closes, 14)
        ema20 = calculate_ema(closes, 20)
        if rsi is None or ema20 is None:
            return None
        if rsi < 40 and current_price > ema20:
            return 'BUY'
        if rsi > 60 and current_price < ema20:
            return 'SELL'
        return None


# ==================== DATABASE ====================

def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA busy_timeout=5000')
    return conn


def record_trade(
    bot_id: str,
    user_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    order_id: str,
    profit: float = 0.0,
) -> None:
    """Record a completed trade in the trades table."""
    try:
        trade_id = str(uuid.uuid4())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO trades
            (trade_id, bot_id, user_id, symbol, order_type, volume, price,
             profit, ticket, time_open, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)
        ''', (
            trade_id, bot_id, user_id, symbol, side.upper(),
            quantity, price, profit, order_id,
            datetime.now().isoformat(),
            datetime.now().isoformat(), datetime.now().isoformat(),
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"record_trade failed ({bot_id}): {e}")


def record_trade_close(
    bot_id: str,
    user_id: str,
    symbol: str,
    side: str,
    quantity: float,
    entry_price: float,
    exit_price: float,
    order_id: str,
    profit: float,
    close_reason: str = 'TP',
) -> None:
    """Mark an open trade as closed with realized profit in the trades table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_iso = datetime.now().isoformat()
        cursor.execute('''
            UPDATE trades
            SET profit = ?,
                status = 'closed',
                time_close = ?,
                updated_at = ?
            WHERE ticket = ? AND bot_id = ? AND status = 'open'
        ''', (profit, now_iso, now_iso, order_id, bot_id))
        if cursor.rowcount == 0:
            trade_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO trades
                (trade_id, bot_id, user_id, symbol, order_type, volume, price,
                 profit, ticket, time_open, time_close, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'closed', ?, ?)
            ''', (
                trade_id, bot_id, user_id, symbol, 'SELL' if side.upper() == 'BUY' else 'BUY',
                quantity, exit_price, profit, order_id,
                now_iso, now_iso, now_iso, now_iso,
            ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"record_trade_close failed ({bot_id}): {e}")


def update_bot_profit(bot_id: str, profit_delta: float) -> None:
    """Update daily/total profit on user_bots table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE user_bots
            SET daily_profit = daily_profit + ?,
                total_profit = total_profit + ?,
                updated_at = ?
            WHERE bot_id = ?
        ''', (profit_delta, profit_delta, datetime.now().isoformat(), bot_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"update_bot_profit failed ({bot_id}): {e}")


# ==================== BOT TRADING LOOP ====================

def _estimate_quantity(client: BinanceClient, symbol: str, usdt_amount: float) -> float:
    """Convert USDT amount to coin quantity for market order."""
    try:
        sym = client.normalize_symbol(symbol)
        if not sym:
            return 0.001
        # Get lot size step from exchange info
        info = client.get_symbol_info(symbol)
        step = 0.001
        min_qty = 0.001
        if info:
            for f in info.get('filters', []):
                if f['filterType'] == 'LOT_SIZE':
                    step = float(f['stepSize'])
                    min_qty = float(f['minQty'])
                    break

        price = get_cached_price(sym) or client.get_price(symbol) or 1.0
        if price <= 0:
            return min_qty

        raw_qty = usdt_amount / price
        # Round down to nearest step
        precision = max(0, -int(math.floor(math.log10(step)))) if step > 0 else 3
        qty = math.floor(raw_qty / step) * step
        qty = round(qty, precision)
        return max(qty, min_qty)
    except Exception:
        return 0.001


def bot_trading_loop(bot_id: str, user_id: str, bot_config: Dict, credentials: Dict) -> None:
    """
    Main trading loop for a single Binance bot.
    Runs in its own thread until bot_stop_flags[bot_id] is True.

    Flow per cycle:
    1. Get price from Redis cache → fallback to Binance REST
    2. Fetch klines for signal generation
    3. Calculate signal (BUY / SELL / None)
    4. If signal: place market order → record trade → update profit
    5. Sleep for trading_interval seconds
    """
    logger.info(f"[Bot {bot_id[:8]}] Trading loop started for user={user_id[:8]}")

    # Extract bot parameters
    symbol = bot_config.get('symbol') or bot_config.get('symbols', 'BTCUSDT')
    if isinstance(symbol, list):
        symbol = symbol[0] if symbol else 'BTCUSDT'
    strategy = bot_config.get('strategy', 'AUTO')
    lot_size_usdt = float(bot_config.get('lot_size') or bot_config.get('riskPerTrade') or 50.0)
    trading_interval = int(bot_config.get('tradingInterval') or DEFAULT_TRADING_INTERVAL)
    is_live = bool(credentials.get('is_live', False))

    api_key = credentials.get('api_key', '')
    api_secret = credentials.get('api_secret', '')

    if not api_key or not api_secret:
        logger.error(f"[Bot {bot_id[:8]}] Missing Binance API key/secret — bot cannot trade")
        return

    client = BinanceClient(api_key, api_secret, is_live=is_live)
    norm_symbol = client.normalize_symbol(symbol)
    if not norm_symbol:
        logger.error(f"[Bot {bot_id[:8]}] Unsupported symbol: {symbol}")
        return

    consecutive_errors = 0
    consecutive_wins = 0
    consecutive_losses = 0
    current_lot_size_usdt = lot_size_usdt
    active_positions: Dict[str, Dict] = {}

    while not bot_stop_flags.get(bot_id, False):
        cycle_start = time.time()
        try:
            # ── 1. Get current price ──────────────────────────────────────────
            current_price = get_cached_price(norm_symbol)
            if current_price is None:
                current_price = client.get_price(norm_symbol)
            if current_price is None or current_price <= 0:
                logger.debug(f"[Bot {bot_id[:8]}] Cannot get price for {norm_symbol}, skipping cycle")
                consecutive_errors += 1
                if consecutive_errors >= 5:
                    logger.warning(f"[Bot {bot_id[:8]}] 5 consecutive errors — sleeping 60s")
                    time.sleep(60)
                    consecutive_errors = 0
                else:
                    time.sleep(10)
                continue

            consecutive_errors = 0

            # ── 2. Check open positions for TP/SL/trailing ──────────────────
            positions_to_close = []
            for pos_id, pos in list(active_positions.items()):
                entry_price = pos['entry_price']
                side = pos['side']
                quantity = pos['quantity']
                highest_price = pos.get('highest_price', entry_price)
                lowest_price = pos.get('lowest_price', entry_price)

                if side == 'BUY':
                    unrealized_pnl_pct = (current_price - entry_price) / entry_price
                    highest_price = max(highest_price, current_price)
                    # Trailing stop: if price pulled back from peak by TRAILING_STOP_PCT
                    trailing_stop_price = highest_price * (1 - TRAILING_STOP_PCT)
                    # Hard stop-loss
                    stop_loss_price = entry_price * (1 - DEFAULT_STOP_LOSS_PCT)
                    # Take-profit
                    take_profit_price = entry_price * (1 + DEFAULT_TAKE_PROFIT_PCT)

                    if current_price >= take_profit_price:
                        positions_to_close.append((pos_id, 'TP', take_profit_price))
                    elif current_price <= stop_loss_price:
                        positions_to_close.append((pos_id, 'SL', stop_loss_price))
                    elif current_price <= trailing_stop_price:
                        positions_to_close.append((pos_id, 'TRAILING', trailing_stop_price))
                else:  # SELL
                    unrealized_pnl_pct = (entry_price - current_price) / entry_price
                    lowest_price = min(lowest_price, current_price)
                    trailing_stop_price = lowest_price * (1 + TRAILING_STOP_PCT)
                    stop_loss_price = entry_price * (1 + DEFAULT_STOP_LOSS_PCT)
                    take_profit_price = entry_price * (1 - DEFAULT_TAKE_PROFIT_PCT)

                    if current_price <= take_profit_price:
                        positions_to_close.append((pos_id, 'TP', take_profit_price))
                    elif current_price >= stop_loss_price:
                        positions_to_close.append((pos_id, 'SL', stop_loss_price))
                    elif current_price >= trailing_stop_price:
                        positions_to_close.append((pos_id, 'TRAILING', trailing_stop_price))

                active_positions[pos_id]['highest_price'] = highest_price
                active_positions[pos_id]['lowest_price'] = lowest_price

            # Close positions that hit TP/SL/trailing
            for pos_id, close_type, close_price in positions_to_close:
                pos = active_positions.pop(pos_id, None)
                if pos is None:
                    continue
                close_side = 'SELL' if pos['side'] == 'BUY' else 'BUY'
                close_result = client.place_market_order(norm_symbol, close_side, pos['quantity'])
                if close_result.get('success'):
                    pnl_pct = (close_price - pos['entry_price']) / pos['entry_price'] if pos['entry_price'] > 0 else 0
                    pnl_usdt = pnl_pct * pos['quantity'] * pos['entry_price']
                    if pnl_usdt > 0:
                        consecutive_wins += 1
                        consecutive_losses = 0
                        # Compound: increase lot size on win streak
                        if consecutive_wins >= LOT_SIZE_RESTORE_AFTER:
                            current_lot_size_usdt = min(lot_size_usdt * (1 + COMPOUND_REINVEST_PCT), MAX_LOT_SIZE_USDT)
                            consecutive_wins = 0
                    else:
                        consecutive_losses += 1
                        consecutive_wins = 0
                        # Reduce lot size on loss streak
                        if consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
                            current_lot_size_usdt = max(lot_size_usdt * LOT_SIZE_REDUCTION_FACTOR, MIN_LOT_SIZE_USDT)
                            consecutive_losses = 0
                    logger.info(
                        f"[Bot {bot_id[:8]}] 📊 {close_type} {norm_symbol} @ {close_price:.4f} | "
                        f"P&L: ${pnl_usdt:.2f} ({pnl_pct*100:.2f}%) | Lot: ${current_lot_size_usdt:.2f}"
                    )
                    # Persist the close: mark trade as closed with realized P&L
                    try:
                        record_trade_close(
                            bot_id=bot_id,
                            user_id=user_id,
                            symbol=norm_symbol,
                            side=pos['side'],
                            quantity=pos['quantity'],
                            entry_price=pos['entry_price'],
                            exit_price=close_price,
                            order_id=pos.get('order_id', ''),
                            profit=pnl_usdt,
                            close_reason=close_type,
                        )
                        update_bot_profit(bot_id, pnl_usdt)
                    except Exception as _close_rec_err:
                        logger.warning(f"[Bot {bot_id[:8]}] Failed to persist close for {norm_symbol}: {_close_rec_err}")
                else:
                    logger.warning(f"[Bot {bot_id[:8]}] Failed to close position {pos_id}: {close_result.get('error')}")

            # ── 3. Fetch klines for signal analysis ──────────────────────────
            klines = client.get_klines(norm_symbol, interval='1h', limit=60)
            if not klines:
                time.sleep(30)
                continue

            # ── 4. Generate signal ──────────────────────────────────────────
            signal = calculate_signal(norm_symbol, strategy, klines, current_price, bot_config)

            if signal is None:
                logger.debug(
                    f"[Bot {bot_id[:8]}] {norm_symbol} @ {current_price:.4f} — no signal ({strategy})"
                )
            else:
                # ── 5. Place order ──────────────────────────────────────────
                quantity = _estimate_quantity(client, norm_symbol, current_lot_size_usdt)
                if quantity <= 0:
                    quantity = 0.001

                logger.info(
                    f"[Bot {bot_id[:8]}] Signal: {signal} {norm_symbol} | "
                    f"price={current_price:.4f} qty={quantity} usdt≈{current_lot_size_usdt:.2f}"
                )

                result = client.place_market_order(norm_symbol, signal, quantity)

                if result['success']:
                    order_id = str(result.get('orderId', ''))
                    fills = result.get('fills', [])
                    filled_price = (
                        float(fills[0]['price']) if fills and fills[0].get('price')
                        else current_price
                    )

                    # Record trade in DB
                    record_trade(
                        bot_id=bot_id,
                        user_id=user_id,
                        symbol=norm_symbol,
                        side=signal,
                        quantity=quantity,
                        price=filled_price,
                        order_id=order_id,
                    )
                    # Track position for TP/SL
                    pos_id = f"{norm_symbol}_{signal}_{order_id[:8]}"
                    active_positions[pos_id] = {
                        'side': signal,
                        'entry_price': filled_price,
                        'quantity': quantity,
                        'highest_price': filled_price,
                        'lowest_price': filled_price,
                        'order_id': order_id,
                    }
                    logger.info(
                        f"[Bot {bot_id[:8]}] ✅ {signal} {quantity} {norm_symbol} "
                        f"@ {filled_price:.4f} | Order: {order_id} | "
                        f"TP={filled_price*(1+DEFAULT_TAKE_PROFIT_PCT):.4f} "
                        f"SL={filled_price*(1-DEFAULT_STOP_LOSS_PCT):.4f}"
                    )
                else:
                    err_code = result.get('code', 0)
                    err_msg = result.get('error', 'unknown')
                    logger.warning(
                        f"[Bot {bot_id[:8]}] ❌ Order failed: {err_msg} (code={err_code})"
                    )
                    # Rate limited? Back off briefly
                    if err_code in (-1003, -1015, 429):
                        logger.warning(f"[Bot {bot_id[:8]}] Rate limited — sleeping 10s")
                        time.sleep(10)
                        continue

        except Exception as cycle_err:
            logger.error(f"[Bot {bot_id[:8]}] Cycle exception: {cycle_err}")
            consecutive_errors += 1

        # ── 6. Sleep until next cycle ──────────────────────────────────
        elapsed = time.time() - cycle_start
        sleep_time = max(5, trading_interval - elapsed)
        # Add small random jitter ±10% to prevent thundering herd
        jitter = random.uniform(-sleep_time * 0.1, sleep_time * 0.1)
        actual_sleep = sleep_time + jitter

        # Check stop flag every 5s during sleep
        slept = 0.0
        while slept < actual_sleep and not bot_stop_flags.get(bot_id, False):
            time.sleep(min(5.0, actual_sleep - slept))
            slept += 5.0

    logger.info(f"[Bot {bot_id[:8]}] Trading loop stopped")


# ==================== BOT LIFECYCLE ====================

def start_bot(bot_id: str, user_id: str, bot_config: Dict, credentials: Dict) -> bool:
    """Start a bot thread. Returns False if worker is at capacity."""
    if len(active_bots) >= MAX_BOTS_PER_WORKER:
        logger.warning(
            f"Worker at capacity ({MAX_BOTS_PER_WORKER} bots) — cannot start bot {bot_id[:8]}"
        )
        return False

    if bot_id in bot_threads and bot_threads[bot_id].is_alive():
        logger.info(f"Bot {bot_id[:8]} already running")
        return True

    bot_stop_flags[bot_id] = False
    active_bots[bot_id] = {**bot_config, 'user_id': user_id, 'started_at': datetime.now().isoformat()}

    t = threading.Thread(
        target=bot_trading_loop,
        args=(bot_id, user_id, bot_config, credentials),
        daemon=True,
        name=f'binance-bot-{bot_id[:8]}',
    )
    t.start()
    bot_threads[bot_id] = t
    logger.info(f"Bot {bot_id[:8]} started — active bots: {len(active_bots)}")
    return True


def stop_bot(bot_id: str) -> None:
    """Signal a bot thread to stop and clean up."""
    bot_stop_flags[bot_id] = True
    active_bots.pop(bot_id, None)

    t = bot_threads.get(bot_id)
    if t and t.is_alive():
        t.join(timeout=15)
    bot_threads.pop(bot_id, None)
    bot_stop_flags.pop(bot_id, None)
    logger.info(f"Bot {bot_id[:8]} stopped — active bots: {len(active_bots)}")


# ==================== WORKER INFRASTRUCTURE ====================

def register_worker() -> None:
    """Register this worker process in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure worker_pool row exists
    cursor.execute('''
        INSERT OR IGNORE INTO worker_pool (worker_id, pid, status, started_at, heartbeat_at, bot_count, account_group)
        VALUES (?, ?, 'running', ?, ?, 0, 'binance')
    ''', (WORKER_INSTANCE_ID, os.getpid(), datetime.now().isoformat(), datetime.now().isoformat()))
    cursor.execute('''
        UPDATE worker_pool
        SET pid = ?, status = 'running', started_at = ?, heartbeat_at = ?, bot_count = 0, account_group = 'binance'
        WHERE worker_id = ?
    ''', (os.getpid(), datetime.now().isoformat(), datetime.now().isoformat(), WORKER_INSTANCE_ID))
    conn.commit()
    conn.close()
    logger.info(f"Worker {WORKER_INSTANCE_ID} registered (PID {os.getpid()})")


def unregister_worker() -> None:
    """Mark worker as stopped."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE worker_pool
            SET status = 'stopped', stopped_at = ?, pid = NULL
            WHERE worker_id = ?
        ''', (datetime.now().isoformat(), WORKER_INSTANCE_ID))
        conn.commit()
        conn.close()
    except Exception:
        pass


def heartbeat_loop() -> None:
    """Background thread — updates heartbeat every HEARTBEAT_INTERVAL seconds."""
    while worker_running:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE worker_pool
                SET heartbeat_at = ?, bot_count = ?, status = 'running'
                WHERE worker_id = ?
            ''', (datetime.now().isoformat(), len(active_bots), WORKER_INSTANCE_ID))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")
        time.sleep(HEARTBEAT_INTERVAL)


def mark_command_processed(command_id: int, status: str = 'done') -> None:
    """Update a worker_bot_queue row as processed."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE worker_bot_queue
            SET status = ?, processed_at = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat(), command_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"mark_command_processed failed: {e}")


def poll_commands() -> None:
    """
    Main command-poll loop. Reads pending commands from worker_bot_queue.

    Commands:
    - start: Parse credentials + config → start_bot()
    - stop:  stop_bot()
    - stop_all: Stop all bots on this worker
    """
    global worker_running

    logger.info(f"Worker {WORKER_INSTANCE_ID} polling for commands every {COMMAND_POLL_INTERVAL}s")

    while worker_running:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Fetch pending commands assigned to this worker (or unassigned broker=binance)
            cursor.execute('''
                SELECT id, bot_id, user_id, command, bot_config, credentials
                FROM worker_bot_queue
                WHERE status = 'pending'
                  AND (worker_id = ? OR (worker_id IS NULL AND account_group = 'binance'))
                ORDER BY id ASC
                LIMIT 20
            ''', (WORKER_INSTANCE_ID,))
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                cmd_id = row['id']
                bot_id = row['bot_id']
                user_id = row['user_id']
                command = row['command']

                try:
                    bot_config = json.loads(row['bot_config'] or '{}')
                    credentials = json.loads(row['credentials'] or '{}')
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in command {cmd_id}")
                    mark_command_processed(cmd_id, 'error')
                    continue

                if command == 'start':
                    ok = start_bot(bot_id, user_id, bot_config, credentials)
                    mark_command_processed(cmd_id, 'done' if ok else 'error')

                elif command == 'stop':
                    stop_bot(bot_id)
                    mark_command_processed(cmd_id, 'done')

                elif command == 'stop_all':
                    for bid in list(active_bots.keys()):
                        stop_bot(bid)
                    mark_command_processed(cmd_id, 'done')

                else:
                    logger.warning(f"Unknown command: {command}")
                    mark_command_processed(cmd_id, 'error')

        except Exception as e:
            logger.error(f"Command poll error: {e}")

        # Prune dead bot threads
        dead = [bid for bid, t in bot_threads.items() if not t.is_alive()]
        for bid in dead:
            bot_threads.pop(bid, None)
            active_bots.pop(bid, None)
            bot_stop_flags.pop(bid, None)

        time.sleep(COMMAND_POLL_INTERVAL)


def handle_shutdown(signum, frame) -> None:
    """Graceful shutdown on SIGTERM / SIGINT."""
    global worker_running
    logger.info(f"Worker {WORKER_INSTANCE_ID} received shutdown signal — stopping all bots")
    worker_running = False
    for bot_id in list(active_bots.keys()):
        bot_stop_flags[bot_id] = True
    # Give threads 10 seconds to finish current cycles
    time.sleep(3)
    unregister_worker()
    sys.exit(0)


def main() -> None:
    """Entry point for the Binance worker process."""
    logger.info(f"{'='*60}")
    logger.info(f"  Zwesta Binance Worker {WORKER_INSTANCE_ID} starting")
    logger.info(f"  DB: {DATABASE_PATH}")
    logger.info(f"  Redis: {REDIS_URL}")
    logger.info(f"  Max bots: {MAX_BOTS_PER_WORKER}")
    logger.info(f"{'='*60}")

    # Test DB connection
    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        logger.error(f"Cannot connect to database: {e}")
        sys.exit(1)

    register_worker()

    # Register shutdown handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    # Start heartbeat thread
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True, name='heartbeat')
    hb_thread.start()

    # Test Redis connection
    r = get_redis_client()
    if r:
        logger.info("Redis price cache: CONNECTED (shared price feed active)")
    else:
        logger.info("Redis price cache: OFFLINE (will use Binance REST per-bot)")

    logger.info(f"Worker {WORKER_INSTANCE_ID} ready — waiting for bot commands")

    try:
        poll_commands()
    except KeyboardInterrupt:
        pass
    finally:
        global worker_running
        worker_running = False
        unregister_worker()
        logger.info(f"Worker {WORKER_INSTANCE_ID} shut down cleanly")


if __name__ == '__main__':
    main()
