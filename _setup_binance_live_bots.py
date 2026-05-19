import requests, json

BASE = 'http://148.113.5.39:9000'
ADMIN = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure', 'Content-Type': 'application/json'}
s = requests.post(BASE + '/api/user/login', json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}

# Disable the 2 losing bots via PATCH
losing_bots = ['bot_1779029679564_b8070b61', 'bot_1778971251604']
for bid in losing_bots:
    r = requests.patch(BASE + '/api/bot/config/' + bid, headers=h, json={'enabled': False}, timeout=60)
    print(f'DISABLE {bid}: {r.status_code} {r.text[:150]}')

# Set $5 USDT on the profitable bot via admin fix-bot-link (runtime_state)
r2 = requests.post(BASE + '/api/admin/fix-bot-link', headers=ADMIN, json={
    'bot_id': 'bot_1779029733318_cf548079',
    'credential_id': '98ffe683-a17f-4362-955f-7bfb84c4f2d9',
    'is_live': 1,
    'broker_account_id': 'Binance_BINANCE-SPOT-vIWjln1z',
    'runtime_state': {
        'tradeAmount': 5.0,
        'displayCurrency': 'USD',
        'accountCurrency': 'USD',
        'riskPercent': 5.0,
        'dynamicSizing': False,
    }
}, timeout=120)
print(f'SET $5 bot_1779029733318_cf548079: {r2.status_code} {r2.text[:300]}')

# Also patch via standard endpoint to update enabled+tradeAmount properly
r3 = requests.patch(BASE + '/api/bot/config/bot_1779029733318_cf548079', headers=h, json={
    'tradeAmount': 5.0,
    'riskPercent': 5.0,
    'dynamicSizing': False,
    'enabled': True,
}, timeout=60)
print(f'PATCH profitable bot: {r3.status_code} {r3.text[:200]}')
