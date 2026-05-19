"""Discover available API endpoints."""
import urllib.request, json

base = 'http://148.113.5.39:9000'
login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json', 'Authorization': 'Bearer zwesta_live_api_key_2026_secure'}

endpoints = [
    '/api/bot/list',
    '/api/bots/list',
    '/api/user/bots',
    '/api/bot/status/bot_1778970971191',
    '/api/bot/info/bot_1778970971191',
    '/api/bot/config/bot_1778970971191',
    '/api/admin/bots',
]
for ep in endpoints:
    req = urllib.request.Request(base + ep, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode())
        print(f'OK {ep}: {str(data)[:200]}')
    except urllib.error.HTTPError as e:
        print(f'{e.code} {ep}')
    except Exception as e:
        print(f'ERR {ep}: {e}')
