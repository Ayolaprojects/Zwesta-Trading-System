import requests, json, time

BASE = 'http://148.113.5.39:9000'
r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
tok = r.json()['session_token']
h = {'X-Session-Token': tok}

GOOD_PP = {
    'enabled': True,
    'activationPercent': 3.0,
    'activationMinProfit': 2.0,
    'breakEvenBufferProfit': 10.0,
    'breakEvenActivationShare': 0.30,
    'breakEvenLockEnabled': True,
    'zeroLossLockEnabled': True,
    'minLockedProfit': 5.0,
    'retraceClosePercent': 10.0,
    'peakProfitHardLockShare': 0.90,
    'portfolioActivationMinProfit': 3.0,
    'closeLosingPositionsWithProfitablePeers': True,
    'loserRotationMinLoss': 0.0,
    'marginTakeProfitPercent': 30.0,
    'switchOnReversal': True,
    'adaptiveByVolatility': True,
    'minimumHoldMinutes': 1.0,
    'protectedSymbolCooldownMinutes': 5.0,
}

# ── 1. Fix Binance DEMO bots: set sane demo trade amounts ──────────────────────
# Demo account has virtual balance. Use $100 per trade for realistic testing.
BINANCE_DEMO_FIXES = {
    'bot_1779029733318_cf548079': {'tradeAmount': 100.0, 'enabled': True},
    'bot_1779029679564_b8070b61': {'tradeAmount': 100.0},
    'bot_1778971251604':          {'tradeAmount': 100.0},
    'bot_1778970971191':          {'tradeAmount': 100.0},
}

print("=== FIXING BINANCE DEMO BOT TRADE AMOUNTS ===")
for bot_id, patch in BINANCE_DEMO_FIXES.items():
    cfg_resp = requests.get(f'{BASE}/api/bot/config/{bot_id}', headers=h, timeout=15).json()
    cfg = cfg_resp.get('config', {})
    cfg.update(patch)
    cfg['profitProtection'] = GOOD_PP
    cfg['intelligentScanner'] = True
    cfg['symbols'] = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    result = requests.patch(f'{BASE}/api/bot/config/{bot_id}', json={'config': cfg}, headers=h, timeout=60)
    print(f"  {bot_id}: HTTP {result.status_code} {result.text[:100]}")

time.sleep(2)

# ── 2. Start the Exness LIVE bot ────────────────────────────────────────────────
EXNESS_BOT = 'bot_1779057251465'
print(f"\n=== STARTING EXNESS LIVE BOT ({EXNESS_BOT}) ===")
start_resp = requests.post(f'{BASE}/api/bot/start', json={'bot_id': EXNESS_BOT}, headers=h, timeout=30)
print(f"  Start: HTTP {start_resp.status_code} {start_resp.text[:200]}")

time.sleep(3)

# ── 3. Start Binance DEMO bots ─────────────────────────────────────────────────
print("\n=== STARTING BINANCE DEMO BOTS ===")
for bot_id in BINANCE_DEMO_FIXES.keys():
    start = requests.post(f'{BASE}/api/bot/start', json={'bot_id': bot_id}, headers=h, timeout=30)
    print(f"  {bot_id}: HTTP {start.status_code} {start.text[:120]}")
    time.sleep(2)

# ── 4. Final verification ──────────────────────────────────────────────────────
time.sleep(5)
print("\n=== FINAL STATUS ===")
all_bots = [EXNESS_BOT] + list(BINANCE_DEMO_FIXES.keys())
for bot_id in all_bots:
    s = requests.get(f'{BASE}/api/bot/config/{bot_id}', headers=h, timeout=15).json()
    cfg = s.get('config', {})
    pp = cfg.get('profitProtection', {})
    print(f"  {bot_id[:35]} running={s.get('running')} broker={cfg.get('brokerName')} tradeAmt={cfg.get('tradeAmount')} bEB={pp.get('breakEvenBufferProfit')}")
