import requests, json

BASE = 'http://148.113.5.39:9000'
ADMIN = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure', 'Content-Type': 'application/json'}

NEW_CRED_ID = '98ffe683-a17f-4362-955f-7bfb84c4f2d9'
BROKER_ACCOUNT_ID = 'Binance_BINANCE-SPOT-vIWjln1z'

BINANCE_BOTS = [
    'bot_1779029733318_cf548079',
    'bot_1779029679564_b8070b61',
    'bot_1778971251604',
]

for bot_id in BINANCE_BOTS:
    r = requests.post(BASE + '/api/admin/fix-bot-link', headers=ADMIN, json={
        'bot_id': bot_id,
        'credential_id': NEW_CRED_ID,
        'is_live': 1,
        'broker_account_id': BROKER_ACCOUNT_ID,
        'runtime_state': {'displayCurrency': 'USD', 'accountCurrency': 'USD'}
    }, timeout=120)
    print(f'{bot_id}: {r.status_code} {r.text[:200]}')
