"""
Fix all three VPS bots for meaningful P/L:

ROOT CAUSE: Binance SPOT $205 trade × 0.4% TP = $0.82 gross
  minus Binance commission 0.2% round trip = $0.41
  Net per winning trade = $0.41 → at 33% win rate = negative EV

FIXES:
  1. Raise Binance tradeAmount $205→$700 (3.4× bigger = $1.40+ net per win)
  2. Remove cross-pairs (ETHBTC, SOLBNB, BNBETH, BNBUSDT) — stick to USDT pairs only
  3. signalThreshold 1→55 — only high-confidence signals
  4. riskPerTrade 30→3 on all bots
  5. managementProfile fast_growth→balanced on all
  6. Exness riskPerTrade 30→3 (flash losses from oversized lots)
  7. maxDailyLoss tuned to give room for 3-4 normal losses before pausing

BOT IDs:
  bot_1778274751313 = Old Binance (11 trades, no open positions) — STOP+FIX+RESTART
  bot_1778283367754 = Exness MT5  (1 trade, no open positions)  — STOP+FIX+RESTART
  bot_1778283164860 = New Binance (3 open positions)            — SKIP until positions close
"""
import requests, json, time

VPS = 'http://148.113.5.39:9000'
r = requests.post(f'{VPS}/api/user/login',
                  json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
r.raise_for_status()
TOKEN = r.json()['session_token']
H = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
print(f"Logged in OK")

def stop_wait_update_start(bid, new_cfg, label):
    print(f"\n{'='*60}")
    print(f"[{label}] Stopping {bid}...")
    r = requests.post(f'{VPS}/api/bot/stop/{bid}', headers=H, timeout=15)
    print(f"  Stop: {r.status_code} {r.text[:80]}")

    print(f"  Waiting 140s for thread to die...")
    for i in range(14):
        time.sleep(10)
        remaining = 130 - i*10
        print(f"    {remaining}s remaining...")

    print(f"  Updating config...")
    r = requests.put(f'{VPS}/api/bot/config/{bid}', headers=H, json=new_cfg, timeout=15)
    print(f"  Config PUT: {r.status_code} {r.text[:150]}")

    if r.status_code == 409:
        print(f"  Thread still alive — waiting another 130s...")
        for i in range(13):
            time.sleep(10)
            remaining = 120 - i*10
            print(f"    {remaining}s remaining...")
        r = requests.put(f'{VPS}/api/bot/config/{bid}', headers=H, json=new_cfg, timeout=15)
        print(f"  Config PUT retry: {r.status_code} {r.text[:150]}")

    if r.status_code in (200, 201):
        print(f"  Starting {bid}...")
        r = requests.post(f'{VPS}/api/bot/start', headers=H, json={'botId': bid}, timeout=15)
        print(f"  Start: {r.status_code} {r.text[:150]}")
        return True
    else:
        print(f"  !! Config update failed — manual intervention needed")
        return False

# ── 1. OLD BINANCE BOT (no open positions) ────────────────────────────────────
# Key changes:
#   tradeAmount: $252 → $700   (3.4× bigger → ~$1.40+ net per winning trade)
#   signalThreshold: 1 → 55    (filter weak signals)
#   riskPerTrade: 30 → 3       (conservative lot sizing)
#   symbols: remove ETHBTC, SOLBNB (cross-pairs, low liquidity, hard to profit)
#   maxDailyLoss: $160 → $90   (3 × $30 stop-outs before pause)
#   managementProfile: balanced
binance_old_cfg = {
    'credentialId': 'bf86a3a3-91e2-4bf4-93a7-13ac3539cbd8',
    'tradeAmount': 700.0,
    'riskPerTrade': 3.0,
    'maxDailyLoss': 90.0,
    'signalThreshold': 55,
    'managementProfile': 'balanced',
    'symbols': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    'maxOpenPositions': 3,
    'dynamicSizing': True,
}
stop_wait_update_start('bot_1778274751313', binance_old_cfg, 'OLD BINANCE')

# ── 2. EXNESS MT5 BOT ─────────────────────────────────────────────────────────
# Key changes:
#   riskPerTrade: 30 → 3       (was causing flash R82 losses per trade)
#   tradeAmount: R856 → R1500  (15% of R10k account — use more capital)
#   maxDailyLoss: R160 → R450  (3 × ~R150 stop-outs before pause)
#   managementProfile: balanced
#   signalThreshold: 72        (keep selective)
exness_cfg = {
    'credentialId': '8a2a185c-eb95-4803-8590-9523ae0a9c4d',
    'tradeAmount': 1500.0,
    'riskPerTrade': 3.0,
    'maxDailyLoss': 450.0,
    'signalThreshold': 72,
    'managementProfile': 'balanced',
    'symbols': ['ETHUSDm', 'BTCUSDm'],
    'maxOpenPositions': 3,
    'dynamicSizing': True,
}
stop_wait_update_start('bot_1778283367754', exness_cfg, 'EXNESS MT5')

# ── 3. NEW BINANCE BOT (has open positions — only update if no open pos) ──────
print(f"\n{'='*60}")
print("[NEW BINANCE] Checking open positions...")
r = requests.get(f'{VPS}/api/bot/status', headers=H, timeout=15)
bots = r.json().get('bots', [])
new_binance = next((b for b in bots if b['botId'] == 'bot_1778283164860'), None)
if new_binance:
    open_pos = new_binance.get('openPositions', [])
    print(f"  Open positions: {len(open_pos)}")
    for p in open_pos:
        print(f"    {p['symbol']} {p['type']} entry={p['entryPrice']} profit={p['profit']}")
    if len(open_pos) == 0:
        new_binance_cfg = {
            'credentialId': 'bf86a3a3-91e2-4bf4-93a7-13ac3539cbd8',
            'tradeAmount': 700.0,
            'riskPerTrade': 3.0,
            'maxDailyLoss': 90.0,
            'signalThreshold': 55,
            'managementProfile': 'balanced',
            'symbols': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
            'maxOpenPositions': 3,
            'dynamicSizing': True,
        }
        stop_wait_update_start('bot_1778283164860', new_binance_cfg, 'NEW BINANCE')
    else:
        print("  Skipping — has open positions. Re-run this script when they close.")
else:
    print("  Bot not found in status response")

# ── Final status ───────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("FINAL STATUS:")
r = requests.get(f'{VPS}/api/bot/status', headers=H, timeout=15)
bots = r.json().get('bots', [])
for b in bots:
    bid = b['botId']
    broker = b.get('broker_type', '?')
    st = b.get('status', '?')
    pause = b.get('pauseReason', '')
    eff = b.get('effectiveTradeAmount', '?')
    trades = b.get('totalTrades', 0)
    pnl = b.get('totalProfit', 0)
    print(f"  {broker} {bid}: {st} | eff={eff} | trades={trades} pnl={pnl}")
    if pause:
        print(f"    pause: {pause}")
