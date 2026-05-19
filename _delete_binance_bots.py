import requests, json

BASE = 'http://148.113.5.39:9000'
s = requests.post(BASE + '/api/user/login', json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}

BINANCE_BOTS = [
    'bot_1779029733318_cf548079',
    'bot_1779029679564_b8070b61',
    'bot_1778971251604',
    'bot_1779122762731',  # newly appeared bot
]

for bid in BINANCE_BOTS:
    r = requests.delete(BASE + '/api/bot/delete/' + bid, headers=h, json={}, timeout=60)
    print(f'DELETE {bid}: {r.status_code} {r.text[:200]}')

# Confirm remaining bots
UID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
r2 = requests.get(BASE + '/api/user/' + UID + '/bots', headers=h, timeout=20)
bots = r2.json().get('bots', [])
print(f'\nRemaining bots: {len(bots)}')
for b in bots:
    print(f"  {b.get('bot_id')} | {b.get('name')} | {b.get('brokerName', b.get('broker','?'))}")
