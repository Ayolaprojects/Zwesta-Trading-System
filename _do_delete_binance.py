import requests, time

BASE = 'http://148.113.5.39:9000'
s = requests.post(BASE + '/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}
UID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

BOTS = [
    'bot_1779131132692_3d47eb9b',
    'bot_1778971251604',
    'bot_1779029679564_b8070b61',
]

for bot_id in BOTS:
    print(f'Deleting {bot_id}...')
    try:
        r = requests.post(f'{BASE}/api/bot/delete/{bot_id}',
                          headers=h, json={'user_id': UID}, timeout=120)
        print(f'  {r.status_code} {r.text[:160]}')
    except Exception as e:
        print(f'  ERROR: {e}')
    time.sleep(2)

# Verify
time.sleep(2)
r = requests.get(f'{BASE}/api/bot/status', headers=h, timeout=20)
data = r.json()
bots = data if isinstance(data, list) else data.get('bots', [])
print(f'\nRemaining bots: {len(bots)}')
for b in bots:
    bid = b.get('botId')
    btype = b.get('broker_type')
    bstatus = b.get('status')
    print(f'  {bid}: {btype} | {bstatus}')
