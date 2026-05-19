"""
Finalise system setup:
- Fix Binance demo bot trade amounts in VPS DB via start/stop + direct config
- Start Exness live bot
- Start Binance demo bots
"""
import requests, json, time, sqlite3

BASE = 'http://148.113.5.39:9000'

def login():
    r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
    return r.json()['session_token']

def headers():
    return {'X-Session-Token': login()}

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

EXNESS_BOT = 'bot_1779057251465'

BINANCE_BOTS = [
    'bot_1779029733318_cf548079',
    'bot_1779029679564_b8070b61',
    'bot_1778971251604',
    'bot_1778970971191',
]

# ── STEP 1: Start Exness LIVE bot ─────────────────────────────────────────────
h = headers()
print(f"\n[1] Starting Exness LIVE bot {EXNESS_BOT} ...")
r = requests.post(f'{BASE}/api/bot/start', json={'bot_id': EXNESS_BOT}, headers=h, timeout=30)
print(f"    HTTP {r.status_code}: {r.text[:200]}")

# ── STEP 2: Fix Binance demo bots via local DB ────────────────────────────────
print("\n[2] Patching Binance demo bot configs in local DB ...")
try:
    db = sqlite3.connect(r'C:\backend\zwesta_trading.db')
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    for bot_id in BINANCE_BOTS:
        cur.execute('SELECT config FROM user_bots WHERE bot_id = ?', (bot_id,))
        row = cur.fetchone()
        if not row:
            print(f"  {bot_id}: NOT FOUND in local DB")
            continue
        try:
            cfg = json.loads(row['config']) if row['config'] else {}
        except Exception:
            cfg = {}
        cfg['tradeAmount'] = 100.0
        cfg['fixedTradeAmount'] = 100.0
        cfg['profitProtection'] = GOOD_PP
        cfg['intelligentScanner'] = True
        cfg['enabled'] = True
        cfg['symbols'] = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        cur.execute('UPDATE user_bots SET config = ?, enabled = 1 WHERE bot_id = ?',
                    (json.dumps(cfg), bot_id))
        print(f"  {bot_id}: patched in local DB")
    db.commit()
    db.close()
    print("  Local DB patched OK")
except Exception as e:
    print(f"  DB error: {e} — will try API PATCH with longer timeout")

# ── STEP 3: Start Binance demo bots ──────────────────────────────────────────
print("\n[3] Starting Binance demo bots ...")
for bot_id in BINANCE_BOTS:
    h = headers()
    # Stop first to pick up any DB changes
    stop = requests.post(f'{BASE}/api/bot/stop/{bot_id}', headers=h, timeout=20)
    print(f"  {bot_id} STOP: {stop.status_code}")
    time.sleep(5)
    h = headers()
    start = requests.post(f'{BASE}/api/bot/start', json={'bot_id': bot_id}, headers=h, timeout=30)
    print(f"  {bot_id} START: {start.status_code} {start.text[:120]}")
    time.sleep(3)

# ── STEP 4: Verify ────────────────────────────────────────────────────────────
time.sleep(5)
print("\n[4] Final verification ...")
h = headers()
for bot_id in [EXNESS_BOT] + BINANCE_BOTS:
    s = requests.get(f'{BASE}/api/bot/config/{bot_id}', headers=h, timeout=15).json()
    cfg = s.get('config', {})
    pp = cfg.get('profitProtection', {})
    print(f"  {bot_id[:35]} running={s.get('running')} broker={cfg.get('brokerName')} amt={cfg.get('tradeAmount')} bEB={pp.get('breakEvenBufferProfit')}")
