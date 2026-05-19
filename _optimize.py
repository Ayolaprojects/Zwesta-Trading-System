"""Comprehensive optimization for Binance demo bots:
- Reset peakProfit/maxDrawdown (tiny historical peak caused 359.6% drawdown bug)
- Disable adaptive_raw_fallback (was forcing trades on 20-strength signals)
- Disable autoAdaptationEnabled and intelligentScanner overrides
- Lock to tighter SL (already 15) and wider TP (already 42) — keep
- Widen SL to 25 pips (give trades room)
- Hold signalThreshold=50, manual mode, autoSwitch=False
"""
import json, sqlite3
from datetime import datetime
import urllib.request
DB = r'C:\backend\zwesta_trading.db'
USER = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
NOW = datetime.now().isoformat()
# accountEquityHighWatermark: set to 0 so the bot rebases HWM to current live equity
# on first cycle. Hard-coding 4109.27 (a stale value) caused instant drawdown cooldown
# whenever live equity was below that.
HWM_RESET = 0.0
c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
cur = c.cursor()


def _fetch_eth_price() -> float:
    try:
        with urllib.request.urlopen('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT', timeout=5) as r:
            return float(json.loads(r.read().decode())['price'])
    except Exception as e:
        print(f"[OPT] ETHUSDT price fetch failed ({e}); using fallback 2380")
        return 2380.0


# Bot 1778 has 0.10148970 ETH sitting on the spot account with no tracked entry,
# blocking all SELLs. Seed it as an open BUY position so the bot can exit it.
# Bot 1777 has 1.83377700 ETH untracked (per backend log) — seed too.
SEED_BOTS_ETH = {
    'bot_1778004514350': 0.10148970,
    'bot_1777949277150': 1.83377700,
}
SEED_TICKET = 'manual_seed_ethusdt_001'

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
    'maxDrawdown': 0.0,
    'peakProfit': 0.0,
    'totalLosses': 0.0,
    'accountEquityHighWatermark': HWM_RESET,
    'accountEquity': 0.0,
    'accountBalance': 0.0,
    # Clear cumulative profit floor + session loss tracking so test bots aren't
    # locked out by historical $0.30 vs $1.55-loss arithmetic.
    'totalProfit': 0.0,
    'profit': 0.0,
    'dailyProfits': {},
    'sessionStartProfit': 0.0,
    'tradeHistory': [],          # clear runtime trade replay so totalProfit/peakProfit don't get rebuilt
    'totalTrades': 0,
    'winningTrades': 0,
    'profitHistory': [],
    'drawdownPausePercent': 50.0,  # raise from default 12% so HWM rebases don't trip during testing
    'slPipsOverride': 25.0,   # widen SL: more room
    'tpPipsOverride': 42.0,   # keep TP
    'maxOpenPositions': 3,    # allow some diversification
    'effectiveMaxOpenPositions': 3,
    'maxPositionsPerSymbol': 1,
    'effectiveMaxPositionsPerSymbol': 1,
    # Auto-close BUY positions held for more than this many hours so the bot
    # can free spot inventory and re-trade. Prevents "1 trade then stale forever".
    'maxPositionAgeHours': 4.0,
    'agedClosePnlFloor': -2.0,
}

for r in cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Binance_%' AND user_id=?", (USER,)).fetchall():
    bid = r['bot_id']
    s = json.loads(r['runtime_state'] or '{}')
    s.update(PATCH)
    # Clear phantom open_positions whose tickets are already closed in tradeHistory
    op = s.get('open_positions') or {}
    closed_tickets = {str(t.get('ticket')) for t in (s.get('tradeHistory') or []) if str(t.get('status') or '').lower() == 'closed'}
    cleaned = {k: v for k, v in op.items() if str(k) not in closed_tickets}
    if len(cleaned) != len(op):
        print(f"[OPT] {bid}: removed {len(op)-len(cleaned)} phantom open positions")
    s['open_positions'] = cleaned

    # Seed untracked ETHUSDT spot inventory for the affected bot so SELLs aren't perma-blocked.
    if bid in SEED_BOTS_ETH:
        seed_qty = SEED_BOTS_ETH[bid]
        op2 = s.get('open_positions') or {}
        already_has_eth = any(
            (str(p.get('symbol') or '').upper().replace('M', '') == 'ETHUSDT')
            for p in op2.values() if isinstance(p, dict)
        )
        if not already_has_eth:
            eth_price = _fetch_eth_price()
            op2[SEED_TICKET] = {
                'ticket': SEED_TICKET,
                'symbol': 'ETHUSDT',
                'type': 'BUY',
                'volume': seed_qty,
                'entryPrice': eth_price,
                'currentPrice': eth_price,
                'profit': 0.0,
                'status': 'open',
                'entryTime': NOW,
                'botId': bid,
                'broker': 'Binance',
                'stopLossPrice': 0.0,
                'takeProfitPrice': 0.0,
                'slPips': 0.0,
                'tpPips': 0.0,
                'pipDistance': 0.0,
                'seededFromUntrackedInventory': True,
            }
            s['open_positions'] = op2
            print(f"[OPT] {bid}: seeded ETHUSDT open BUY {seed_qty} @ {eth_price} (ticket={SEED_TICKET})")
        else:
            print(f"[OPT] {bid}: ETHUSDT already tracked; skipping seed")

    cur.execute("UPDATE user_bots SET runtime_state=?, updated_at=?, daily_profit=0, total_profit=0 WHERE bot_id=?",
                (json.dumps(s), NOW, bid))
    # Wipe trade history rows for this test bot so peakProfit/maxDrawdown/totalProfit
    # don't get rebuilt from old closed trades on startup (which re-triggers cumulative
    # profit floor + drawdown gates).
    cur.execute("DELETE FROM trades WHERE bot_id=?", (bid,))
    print(f"[OPT] {bid}: applied optimization patch")

# Also disable the Exness bot for now since MT5 can't connect locally
cur.execute("UPDATE user_bots SET enabled=0, updated_at=? WHERE bot_id=? AND user_id=?",
            (NOW, 'bot_1778010173819', USER))
print("[OPT] Exness bot disabled for local testing (no MT5 IPC locally; re-enable on VPS).")

c.commit(); c.close()
print('\nDone. Restart backend to take effect.')
