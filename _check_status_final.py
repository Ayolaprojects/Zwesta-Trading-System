import requests, time

BASE = 'http://148.113.5.39:9000'
s = requests.post(BASE + '/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}

r = requests.post(f'{BASE}/api/bots/runtime/prune-ghosts', headers=h, timeout=20)
print('prune:', r.status_code, r.text[:200])

time.sleep(2)
r = requests.get(f'{BASE}/api/bot/status', headers=h, timeout=20)
data = r.json()
bots = data if isinstance(data, list) else data.get('bots', [])
print(f'Remaining bots: {len(bots)}')
for b in bots:
    bid = b.get('botId')
    btype = b.get('broker_type')
    bstatus = b.get('status')
    print(f'  {bid}: {btype} | {bstatus}')
