import requests
BASE = 'http://148.113.5.39:9000'
USER = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
print('Login:', r.status_code)
tok = r.json()['session_token']
h = {'X-Session-Token': tok}
bots = requests.get(f'{BASE}/api/bot/status', headers=h, timeout=10).json()
print('Active bots:')
for b in bots.get('bots', []):
    bid  = b.get('botId','')[:32]
    st   = b.get('status','?')
    bal  = b.get('accountBalance',0)
    curr = b.get('displayCurrency','?')
    print(f'  {bid} [{st}] bal={bal} {curr}')
