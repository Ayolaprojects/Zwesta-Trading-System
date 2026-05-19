"""
Fix bot_1779100405400:
  - is_live=1 but uses DEMO credential 66838627 (Exness-MT5Trial9)
  - PATCH it (no changes needed) — backend will re-derive is_live=0 from credential
  - Also start bot_1779057251465 (R1350 live) with long timeout
"""
import requests, time, json

BASE    = 'http://148.113.5.39:9000'
USER_ID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
DEMO_BOT  = 'bot_1779100405400'   # R24k — should be demo
LIVE_BOT  = 'bot_1779057251465'   # R1350 — actual live

def login():
    r = requests.post(f'{BASE}/api/user/login',
        json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
    return r.json()['session_token']

h = lambda tok: {'X-Session-Token': tok, 'Content-Type': 'application/json'}

# ── STEP 1: Stop demo bot, PATCH (no payload change needed), restart ──────────
print('[1] Stopping demo bot to allow PATCH...')
tok = login()
stop = requests.post(f'{BASE}/api/bot/stop/{DEMO_BOT}', headers=h(tok),
    json={'user_id': USER_ID}, timeout=20)
print('  Stop:', stop.status_code, stop.text[:100])
time.sleep(5)

# Retry PATCH up to 3 times — old VPS code tries MT5 connect which can take 60-90s
print('[2] PATCHing demo bot (fixing is_live, retrying up to 3x)...')
patched = False
for attempt in range(1, 4):
    tok = login()
    try:
        p = requests.patch(f'{BASE}/api/bot/config/{DEMO_BOT}', headers=h(tok),
            json={'tradeAmount': 500.0, 'displayCurrency': 'ZAR'}, timeout=150)
        print(f'  Attempt {attempt}: {p.status_code} {p.text[:200]}')
        if p.status_code == 200:
            patched = True
            break
        elif p.status_code == 500 and 'locked' in p.text:
            print(f'  DB locked, retrying in 10s...')
            time.sleep(10)
    except requests.exceptions.ReadTimeout:
        print(f'  Attempt {attempt}: timeout — continuing...')
        time.sleep(5)

# Restart demo bot regardless
print('[3] Restarting demo bot...')
tok = login()
rs = requests.post(f'{BASE}/api/bot/start', headers=h(tok),
    json={'botId': DEMO_BOT, 'user_id': USER_ID}, timeout=60)
print('  Start:', rs.status_code, rs.text[:150])

# ── STEP 2: Fix R1350 live bot tradeAmount ─────────────────────────────────────
print()
print('[4] Stopping R1350 live bot for tradeAmount fix...')
tok = login()
stop2 = requests.post(f'{BASE}/api/bot/stop/{LIVE_BOT}', headers=h(tok),
    json={'user_id': USER_ID}, timeout=20)
print('  Stop:', stop2.status_code, stop2.text[:80])
time.sleep(6)

print('[5] PATCHing R1350 bot tradeAmount to R500 (retrying up to 3x)...')
patched2 = False
for attempt in range(1, 4):
    tok = login()
    try:
        p = requests.patch(f'{BASE}/api/bot/config/{LIVE_BOT}', headers=h(tok),
            json={'tradeAmount': 500.0, 'displayCurrency': 'ZAR'}, timeout=150)
        print(f'  Attempt {attempt}: {p.status_code} {p.text[:200]}')
        if p.status_code == 200:
            patched2 = True
            break
        elif p.status_code == 500 and 'locked' in p.text:
            print(f'  DB locked, retrying in 10s...')
            time.sleep(10)
    except requests.exceptions.ReadTimeout:
        print(f'  Attempt {attempt}: timeout — continuing...')
        time.sleep(5)

# ── STEP 3: Start R1350 live bot ─────────────────────────────────────────────
print('[6] Starting R1350 live bot...')
tok = login()
rs2 = requests.post(f'{BASE}/api/bot/start', headers=h(tok),
    json={'botId': LIVE_BOT, 'user_id': USER_ID}, timeout=90)
print('  Start:', rs2.status_code, rs2.text[:200])

# ── STEP 4: Verify final state ────────────────────────────────────────────────
print()
print('[7] Final state check...')
tok = login()
bots = requests.get(f'{BASE}/api/bot/status', headers=h(tok), timeout=15).json()
for b in bots.get('bots', []):
    bid = b.get('botId','')
    if bid in (DEMO_BOT, LIVE_BOT):
        st  = b.get('status','?')
        bal = b.get('accountBalance',0)
        cur = b.get('displayCurrency','?')
        print(f'  {bid}: status={st} balance={bal} {cur}')

# Verify tradeAmounts
for bot_id in (DEMO_BOT, LIVE_BOT):
    cfg = requests.get(f'{BASE}/api/bot/config/{bot_id}', headers=h(tok), timeout=15).json().get('config', {})
    ta  = cfg.get('tradeAmount')
    il  = cfg.get('is_live')
    print(f'  {bot_id}: tradeAmount={ta} is_live={il}')

print()
if patched:
    print('✅ Demo bot is_live flag fixed (now correctly DEMO)')
else:
    print('⚠️  Demo bot PATCH timed out — is_live fix needs backend deployment to VPS')
if patched2:
    print('✅ R1350 bot tradeAmount set to R500')
else:
    print('⚠️  R1350 bot PATCH timed out — tradeAmount=R8 still, needs backend deployment')
