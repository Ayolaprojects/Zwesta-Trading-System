import requests, json
BASE = 'http://148.113.5.39:9000'
r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
tok = r.json()['session_token']
h = {'X-Session-Token': tok}

# ── New R24k bot config ──────────────────────────────────────────────────────
cfg = requests.get(f'{BASE}/api/bot/config/bot_1779100405400', headers=h, timeout=15).json().get('config', {})
print('=== bot_1779100405400 ===')
for k in ['brokerName','credentialId','displayCurrency','accountCurrency','tradeAmount','symbols','riskPerTrade','is_live']:
    print(' ', k, ':', cfg.get(k))

# ── Open positions ────────────────────────────────────────────────────────────
pos = requests.get(f'{BASE}/api/bot/bot_1779100405400/positions', headers=h, timeout=15)
print('\n=== POSITIONS ===')
try:
    print(json.dumps(pos.json(), indent=2)[:1000])
except Exception as e:
    print(pos.status_code, pos.text[:300])

# ── Exness R1350 bot ──────────────────────────────────────────────────────────
print('\n=== Exness R1350 bot ===')
bots = requests.get(f'{BASE}/api/bot/status', headers=h, timeout=15).json()
for b in bots.get('bots', []):
    bid = b.get('botId','')
    if bid == 'bot_1779057251465':
        st = b.get('status')
        ru = b.get('running')
        tr = b.get('totalTrades')
        print(' status:', st, 'running:', ru, 'trades:', tr)
