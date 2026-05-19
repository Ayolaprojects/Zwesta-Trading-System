"""
Restart all bots on VPS using correct botId parameter.
Also fix tradeAmount=None on bot_1778970971191 via PATCH first.
"""
import requests, json, time

BASE = 'http://148.113.5.39:9000'
USER_ID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

def login():
    r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
    return r.json()['session_token']

EXNESS_BOT   = 'bot_1779057251465'   # Exness LIVE
BINANCE_BOTS = [
    'bot_1779029733318_cf548079',   # Binance demo, $500 trade
    'bot_1779029679564_b8070b61',   # Binance demo, $8265 -> will fix to $100
    'bot_1778971251604',             # Binance demo, $800 -> will fix to $100
    'bot_1778970971191',             # Binance demo, None -> will fix to $100
]

ALL_BOTS = [EXNESS_BOT] + BINANCE_BOTS

# ── STEP 1: Stop all bots ─────────────────────────────────────────────────────
print("[1] Stopping all bots ...")
tok = login()
h = {'X-Session-Token': tok}
for bot_id in ALL_BOTS:
    r = requests.post(f'{BASE}/api/bot/stop/{bot_id}', headers=h, timeout=15)
    print(f"    STOP {bot_id[:30]}: {r.status_code}")
time.sleep(8)

# ── STEP 2: Fix tradeAmount on problematic Binance bots ──────────────────────
# NOTE: backend code was fixed to skip BinanceConnection.connect() when credential
# is not changing — so these PATCHes are now fast. Exness bot tradeAmount is fine.
print("\n[2] Patching trade amounts on Binance demo bots ...")
BINANCE_FIXES = {
    'bot_1779029679564_b8070b61': {'tradeAmount': 100.0},
    'bot_1778971251604':          {'tradeAmount': 100.0},
    'bot_1778970971191':          {'tradeAmount': 100.0, 'fixedTradeAmount': 100.0},
}

tok = login()
h = {'X-Session-Token': tok}
for bot_id, patch in BINANCE_FIXES.items():
    cfg_resp = requests.get(f'{BASE}/api/bot/config/{bot_id}', headers=h, timeout=15)
    if cfg_resp.status_code != 200:
        print(f"    {bot_id[:30]}: config fetch failed {cfg_resp.status_code}")
        continue
    cfg = cfg_resp.json().get('config', {})
    for k, v in patch.items():
        cfg[k] = v
    result = requests.patch(f'{BASE}/api/bot/config/{bot_id}', json={'config': cfg}, headers=h, timeout=30)
    print(f"    PATCH {bot_id[:30]}: HTTP {result.status_code} {result.text[:80]}")

time.sleep(5)

# ── STEP 3: Start all bots ────────────────────────────────────────────────────
print("\n[3] Starting all bots ...")
for bot_id in ALL_BOTS:
    tok = login()
    h = {'X-Session-Token': tok}
    body = {'botId': bot_id, 'user_id': USER_ID}
    r = requests.post(f'{BASE}/api/bot/start', json=body, headers=h, timeout=45)
    print(f"    START {bot_id[:30]}: HTTP {r.status_code} {r.text[:150]}")
    time.sleep(3)

# ── STEP 4: Verify ────────────────────────────────────────────────────────────
time.sleep(8)
print("\n[4] Verification ...")
tok = login()
h = {'X-Session-Token': tok}
for bot_id in ALL_BOTS:
    s = requests.get(f'{BASE}/api/bot/config/{bot_id}', headers=h, timeout=15).json()
    cfg = s.get('config', {})
    pp = cfg.get('profitProtection', {})
    print(f"    {bot_id[:35]}  running={s.get('running')}  broker={cfg.get('brokerName')}  amt={cfg.get('tradeAmount')}  bEB={pp.get('breakEvenBufferProfit')}")
