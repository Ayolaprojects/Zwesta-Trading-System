import requests, json

BASE = 'http://148.113.5.39:9000'
s = requests.post(BASE + '/api/user/login', json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}

# 90.7 USDT balance -> 5% = ~$4.54 per trade (safe for small account)
r = requests.post(BASE + '/api/bot/create', headers=h, json={
    'credentialId': '98ffe683-a17f-4362-955f-7bfb84c4f2d9',
    'mode': 'live',
    'name': 'Trend Following Live',
    'strategy': 'Trend Following',
    'symbols': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    'tradeAmount': 5.0,
    'riskPercent': 5.0,
    'dynamicSizing': False,
    'maxOpenPositions': 1,
    'maxOpenTrades': 1,
    'enabled': True,
    'autoAdaptationEnabled': False,
}, timeout=120)

print('status:', r.status_code)
d = r.json()
print(json.dumps(d, indent=2)[:800])
