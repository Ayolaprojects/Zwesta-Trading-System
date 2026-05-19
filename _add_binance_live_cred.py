import requests, json

BASE = 'http://148.113.5.39:9000'

s = requests.post(BASE + '/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}
print('Logged in:', bool(token))

body = {
    'broker_name': 'Binance',
    'api_key': 'VxufaJaSzawkDws0ZdvKvokZGfRPSkkNbIe3vdfki4Vy48ek2M8DEHmzvIWjln1z',
    'api_secret': 'PXVGwsPHxGvLiSjDBgjZdalIFWCeAeKLB4WKaLZKyaadvbJGbwpnbkKUr9pCFtir',
    'server': 'spot',
    'is_live': True,
    'label': 'Binance Spot Live'
}

r = requests.post(BASE + '/api/broker/credentials', headers=h, json=body, timeout=90)
print('status:', r.status_code)
print(r.text[:800])
