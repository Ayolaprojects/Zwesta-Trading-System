import requests

BASE = 'http://148.113.5.39:9000'
ADMIN_KEY = 'zwesta_live_api_key_2026_secure'
s = requests.post(BASE + '/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=20)
token = s.json().get('session_token','')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}
ah = {'Authorization': 'Bearer ' + ADMIN_KEY, 'Content-Type': 'application/json'}
USER_ID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

OLD_BOTS = ['bot_1778971251604', 'bot_1779029679564_b8070b61']

print("Step 1: Clear phantom open_positions via admin patch (so delete won't try to close them)")
for bid in OLD_BOTS:
    r = requests.post(BASE + '/api/admin/fix-bot-link', headers=ah, timeout=20, json={
        'bot_id': bid,
        'runtime_state': {
            'open_positions': {},
            'openPositions': [],
            'enabled': False
        }
    })
    print(f'  Clear positions {bid}: {r.status_code} {r.text[:200]}')

print()
print("Step 2: Delete old demo-promoted bots")
for bid in OLD_BOTS:
    r = requests.post(BASE + '/api/bot/delete/' + bid, headers=h, timeout=60,
                      json={'user_id': USER_ID})
    print(f'  Delete {bid}: {r.status_code} {r.text[:300]}')

print()
print("Step 3: Stop active Binance spot bot")
r = requests.post(BASE + '/api/bot/stop/bot_1779131132692_3d47eb9b', headers=h, timeout=30, json={})
print(f'  Stop: {r.status_code} {r.text[:200]}')
