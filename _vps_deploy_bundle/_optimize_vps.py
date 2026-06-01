"""VPS optimize script: applies the same threshold=2/manual/$50 trade-size patch
to all Binance bots for the active user on the VPS DB.

Usage on VPS (RDP in, then):
    cd C:\backend
    python _optimize_vps.py

Mirrors what _optimize.py does on the local machine, but tuned for VPS:
- $50 trade amount per position (small/safe demo testing)
- Does NOT seed phantom ETH inventory (those bots are real, not test fixtures)
- Does NOT delete from `trades` table (preserve real trade history on VPS)
- Does NOT clear tradeHistory/profitHistory (keep real stats)
- Still resets HWM=0 so equity baseline rebuilds, and clears stale pause flags.
"""
import json, sqlite3
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()
TARGET_BOT_ID = 'bot_1779229018996'
TARGET_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

# Same user as local. Update if VPS user_id differs.
USER = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

PATCH = {
    'signalThreshold': 2,
    'effectiveSignalThreshold': 2,
    'signalThresholdMode': 'manual',
    'autoSwitch': False,
    'autoAdaptationEnabled': False,
    'allowAdaptiveRawFallback': False,
    'intelligentScanner': False,
    'adaptiveSignalThresholdOffset': 0,
    'adaptiveSignalMissCount': 0,
    'adaptiveSignalThresholdReason': None,
    'managementState': 'normal',
    'consecutiveLosses': 0,
    'lossStreakPauseUntil': None,
    'pauseReason': None,
    'drawdownPauseUntil': None,
    'drawdownPauseSetAt': None,
    'accountEquityHighWatermark': 0.0,   # let backend rebase from live equity
    'drawdownPausePercent': 15.0,        # production-safe vs local's 50%
    'tradeAmount': 50.0,                 # $50 per position
    'slPipsOverride': 25.0,
    'tpPipsOverride': 42.0,
    'maxOpenPositions': 3,
    'effectiveMaxOpenPositions': 3,
    'maxPositionsPerSymbol': 1,
    'effectiveMaxPositionsPerSymbol': 1,
    # Auto-close BUY positions held for more than this many hours so the bot
    # can free spot inventory and re-trade. Prevents "1 trade then stale forever".
    'maxPositionAgeHours': 4.0,
    'agedClosePnlFloor': -2.0,
}

TARGET_BOT_OVERRIDE = {
    'managementMode': 'manual',
    'signalThresholdMode': 'manual',
    'managementProfile': 'small_account',
    'managementState': 'manual',
    'signalThreshold': 24,
    'effectiveSignalThreshold': 24,
    'maxOpenPositions': 2,
    'effectiveMaxOpenPositions': 2,
    'maxPositionsPerSymbol': 1,
    'effectiveMaxPositionsPerSymbol': 1,
    'intelligentScanner': True,
    'allowedVolatility': ['Very Low', 'Low', 'Medium'],
    'effectiveAllowedVolatility': ['Very Low', 'Low', 'Medium'],
    'autoSwitch': False,
    'autoAdaptationEnabled': False,
    'allowAdaptiveRawFallback': False,
    'symbols': TARGET_SYMBOLS,
}


def resolve_trade_amount(runtime_state):
    for key in ('tradeAmount', 'effectiveTradeAmount'):
        try:
            value = float(runtime_state.get(key))
        except Exception:
            continue
        if value > 0:
            return value
    return float(PATCH['tradeAmount'])


def build_neutral_sizing_state(now_iso):
    return {
        'timestamp': now_iso,
        'state': 'manual',
        'multiplier': 1.0,
        'scannerCapitalMultiplier': 1.0,
        'reason': 'manual tuned override',
    }


def build_trade_amount_adaptation(now_iso, trade_amount):
    return {
        'timestamp': now_iso,
        'state': 'manual',
        'multiplier': 1.0,
        'scannerCapitalMultiplier': 1.0,
        'baseTradeAmount': trade_amount,
        'adjustedTradeAmount': trade_amount,
        'dailyProfit': 0.0,
        'dailyProfitPeak': 0.0,
        'retraceRatio': 0.0,
        'reason': 'manual tuned override',
    }

c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row
cur = c.cursor()

rows = cur.execute(
    "SELECT bot_id, runtime_state, symbols FROM user_bots "
    "WHERE broker_account_id LIKE 'Binance_%' AND user_id = ?",
    (USER,),
).fetchall()

for r in rows:
    bid = r['bot_id']
    s = json.loads(r['runtime_state'] or '{}')
    original_trade_amount = resolve_trade_amount(s)
    s.update(PATCH)
    if bid == TARGET_BOT_ID:
        s.update(TARGET_BOT_OVERRIDE)
        s['tradeAmount'] = original_trade_amount
        s['effectiveTradeAmount'] = original_trade_amount
        s['lastSizingAdjustment'] = build_neutral_sizing_state(NOW)
        s['tradeAmountAdaptation'] = build_trade_amount_adaptation(NOW, original_trade_amount)
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, symbols=?, updated_at=? WHERE bot_id=?",
            (json.dumps(s), json.dumps(TARGET_SYMBOLS), NOW, bid),
        )
        print(f"[VPS-OPT] {bid}: applied tuned override (threshold=24, scanner on, Medium-or-lower volatility)")
        continue
    cur.execute(
        "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
        (json.dumps(s), NOW, bid),
    )
    print(f"[VPS-OPT] {bid}: applied threshold=2 manual + $50 trade size + HWM rebase")

c.commit()
c.close()
print(f"\nDone. Patched {len(rows)} bot(s). Restart backend (waitress) for changes to take effect.")
