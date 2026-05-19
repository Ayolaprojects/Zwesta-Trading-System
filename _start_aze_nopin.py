"""Start AZE BOT without PIN (backward compat mode)"""
import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
uid = d.get('user_id','')
SH = {'X-Session-Token': token}

print(f'Starting AZE BOT without PIN (backward compat)...')
try:
    r = requests.post(f'{BASE}/api/bot/start', headers=SH,
                      json={'botId': 'AZE BOT', 'bot_id': 'AZE BOT', 'user_id': uid},
                      timeout=40)
    print(f'Status: {r.status_code}')
    print(r.text[:400])
except Exception as e:
    print(f'Error: {e}')
