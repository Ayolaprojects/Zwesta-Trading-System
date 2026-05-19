"""
Use admin API to diagnose VPS bot state and find the database path.
"""
import requests, json

VPS = 'http://148.113.5.39:9000'
API_KEY = 'zwesta_live_api_key_2026_secure'
ADMIN_HEADERS = {'Authorization': f'Bearer {API_KEY}'}

# Login for session token too
response = requests.post(f'{VPS}/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
data = response.json()
SESSION_TOKEN = data['session_token']
USER_ID = data.get('user_id') or data.get('userId') or data.get('id')
SESSION_HEADERS = {'X-Session-Token': SESSION_TOKEN, 'Content-Type': 'application/json'}

print('user_id:', USER_ID)

for bot_id in ['bot_1778970971191', 'bot_1778971251604']:
    print('\n===', bot_id, '===')
    r = requests.get(f'{VPS}/api/admin/bot-daily-loss-debug',
        headers=ADMIN_HEADERS, params={'bot_id': bot_id}, timeout=15)
    print('Admin debug status:', r.status_code)
    if r.status_code == 200:
        info = r.json()
        print('  DB path:', info.get('databasePath'))
        print('  stateSource:', info.get('stateSource'))
        diag = info.get('diagnostics', {})
        print('  diagnostics keys:', list(diag.keys())[:10])
        print('  diagnostics:', json.dumps(diag, indent=2)[:600])
    else:
        print('  Response:', r.text[:200])
