import requests, json, time

BASE = 'http://148.113.5.39:9000'
EXNESS_BOT = 'bot_1779057251465'
USER_ID    = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
tok = r.json()['session_token']
h = {'X-Session-Token': tok, 'Content-Type': 'application/json'}

# 1. Stop
print('[1] Stopping bot...')
stop = requests.post(f'{BASE}/api/bot/stop/{EXNESS_BOT}', headers=h, json={'user_id': USER_ID}, timeout=20)
print('  ', stop.status_code, stop.text[:150])
time.sleep(2)

# 2. Patch trade amount
print('[2] Patching tradeAmount to R500...')
patch = requests.patch(f'{BASE}/api/bot/config/{EXNESS_BOT}', headers=h,
    json={'tradeAmount': 500.0, 'displayCurrency': 'ZAR'}, timeout=30)
print('  ', patch.status_code, patch.text[:300])

# 3. Re-save credential to capture ZAR currency
print('[3] Re-saving credential...')
cred_payload = {
    'broker_name': 'Exness',
    'accountNumber': '295677214',
    'password': 'Ithemba@2026',
    'server': 'Exness-MT5Real27',
    'isLive': True,
    'label': 'Exness ZAR Live',
}
cred_resp = requests.post(f'{BASE}/api/broker/credentials', headers=h, json=cred_payload, timeout=60)
print('  ', cred_resp.status_code, cred_resp.text[:400])

# 4. Verify config
print('[4] Verifying config...')
cfg = requests.get(f'{BASE}/api/bot/config/{EXNESS_BOT}', headers=h, timeout=15).json().get('config', {})
ta = cfg.get('tradeAmount')
dc = cfg.get('displayCurrency')
ac = cfg.get('accountCurrency')
print('  tradeAmount:', ta, '  displayCurrency:', dc, '  accountCurrency:', ac)
