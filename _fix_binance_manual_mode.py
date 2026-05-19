"""
Fix Binance bots by setting managementMode to 'manual'.
This bypasses assisted profile computation that restricts allowedVolatility to ['Very Low', 'Low'].
The DB config has allowedVolatility: ['Low', 'Medium'] which will be used directly in manual mode.
"""
import requests, json

VPS = 'http://148.113.5.39:9000'
response = requests.post(f'{VPS}/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
TOKEN = response.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
print('Authenticated. Token:', TOKEN[:30] + '...')

BINANCE_BOTS = ['bot_1778970971191', 'bot_1778971251604']

for bot_id in BINANCE_BOTS:
    r = requests.get(f'{VPS}/api/bot/config/' + bot_id, headers=HEADERS, timeout=10)
    cfg = r.json().get('config', {})
    print('\n' + bot_id)
    print('  managementMode (before):', cfg.get('managementMode'))
    print('  allowedVolatility:', cfg.get('allowedVolatility'))
    print('  managementProfile:', cfg.get('managementProfile'))

    # Switch to manual mode so raw allowedVolatility from DB is used
    patch = {
        'managementMode': 'manual',
        'allowedVolatility': ['Low', 'Medium', 'High'],  # Set explicitly to include Medium
        'signalThresholdMode': 'manual',  # Keep signal threshold manual
    }
    pr = requests.patch(f'{VPS}/api/bot/config/' + bot_id, headers=HEADERS, json=patch, timeout=10)
    print('  PATCH -> status:', pr.status_code)
    if pr.status_code == 200:
        print('  SUCCESS')
    else:
        print('  RESPONSE:', pr.text[:200])
