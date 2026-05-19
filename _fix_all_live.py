"""Fix AZE BOT (patch lost after DB reload) and bot_1779201336253 (no tradeAmount)."""
import requests, json, time

BASE = 'http://148.113.5.39:9000'
AH = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure', 'Content-Type': 'application/json'}
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}

# --- FIX 1: AZE BOT ---
# Stop it first so patch applies cleanly
print('Stopping AZE BOT...')
r = requests.post(f'{BASE}/api/bot/stop/AZE%20BOT', headers=SH, timeout=15)
print(f'  stop: {r.status_code}')
time.sleep(2)

print('Patching AZE BOT via admin fix-bot-link...')
r = requests.post(f'{BASE}/api/admin/fix-bot-link', headers=AH, json={
    'bot_id': 'AZE BOT',
    'runtime_state': {
        'tradeAmount': 20.0,
        'intelligentScanner': True,
        'allowedVolatility': ['Low', 'Medium', 'High'],
        'tradeAmountAdaptation': None,
        'dailyProfitPeaks': {},
        'effectiveTradeAmount': None,
    }
}, timeout=25)
print(f'  admin patch: {r.status_code} {r.text[:200]}')
time.sleep(1)

# --- FIX 2: bot_1779201336253 - set tradeAmount ---
print('\nPatching bot_1779201336253 via admin fix-bot-link...')
r2 = requests.post(f'{BASE}/api/admin/fix-bot-link', headers=AH, json={
    'bot_id': 'bot_1779201336253',
    'runtime_state': {
        'tradeAmount': 146.0,   # same level as bot_1779185407301 (~7% of R2145 balance)
        'tradeAmountAdaptation': None,
        'dailyProfitPeaks': {},
        'effectiveTradeAmount': None,
    }
}, timeout=25)
print(f'  admin patch: {r2.status_code} {r2.text[:200]}')
time.sleep(2)

# --- Start AZE BOT without PIN ---
print('\nStarting AZE BOT...')
lr2 = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token2 = lr2.json().get('session_token',''); uid = lr2.json().get('user_id','')
SH2 = {'X-Session-Token': token2}
r3 = requests.post(f'{BASE}/api/bot/start', headers=SH2,
                   json={'botId': 'AZE BOT', 'bot_id': 'AZE BOT', 'user_id': uid}, timeout=40)
print(f'  start: {r3.status_code} {r3.text[:200]}')
time.sleep(4)

# --- Verify ---
print('\n=== VERIFICATION ===')
for bot_id in ['AZE BOT', 'bot_1779201336253']:
    rv = requests.get(f'{BASE}/api/bot/config/{requests.utils.quote(bot_id)}', headers=SH2, timeout=10)
    cfg = rv.json().get('config', {})
    print(f"{bot_id}: enabled={cfg.get('enabled')} tradeAmount={cfg.get('tradeAmount')} "
          f"effectiveTradeAmount={cfg.get('effectiveTradeAmount')} scanner={cfg.get('intelligentScanner')}")
