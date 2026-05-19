import requests, time

BASE = 'http://148.113.5.39:9000'
BOT = 'bot_1779131132692_3d47eb9b'
UID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

s = requests.post(BASE + '/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=20)
token = s.json().get('session_token','')
print('token:', token[:20] if token else 'NONE')
h = {'X-Session-Token': token, 'Content-Type': 'application/json'}

# Stop the bot
r = requests.post(f'{BASE}/api/bot/stop/{BOT}', headers=h, json={'user_id': UID})
print('stop:', r.status_code, r.text[:200])
time.sleep(3)

# Restart without PIN (backward-compat mode)
r = requests.post(f'{BASE}/api/bot/start', headers=h, json={
    'botId': BOT,
    'user_id': UID,
})
print('start:', r.status_code, r.text[:300])

