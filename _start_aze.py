"""Start AZE BOT after config was patched in memory"""
import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}

# Request activation pin
print('Requesting activation pin...')
r = requests.post(f'{BASE}/api/bot/AZE%20BOT/request-activation', headers={**SH, 'Content-Type': 'application/json'}, json={}, timeout=15)
print(f'Status: {r.status_code} {r.text[:200]}')
pin_data = r.json() if r.ok else {}
pin = pin_data.get('activation_pin','')
print(f'Pin: {pin}')

if pin:
    print('Starting bot...')
    r2 = requests.post(f'{BASE}/api/bot/start', headers=SH,
                       json={'bot_id': 'AZE BOT', 'activation_pin': pin}, timeout=30)
    print(f'Start: {r2.status_code} {r2.text[:300]}')
else:
    print('No pin returned')
