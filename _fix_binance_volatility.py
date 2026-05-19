"""
Fix Binance bots by adding 'Medium' to allowedVolatility.
This unblocks the 43/100 signal trades that were being blocked by the volatility filter.
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
    r = requests.get(f'{VPS}/api/bot/config/{bot_id}', headers=HEADERS, timeout=10)
    data = r.json()
    cfg = data.get('config', {})
    current_vol = cfg.get('allowedVolatility') or []
    effective_vol = cfg.get('effectiveAllowedVolatility') or []
    print(f'\n{bot_id}:')
    print(f'  allowedVolatility: {current_vol}')
    print(f'  effectiveAllowedVolatility: {effective_vol}')
    print(f'  signalThreshold: {cfg.get("signalThreshold")}')

    # Add Medium if not present
    if 'Medium' not in current_vol:
        new_vol = list(current_vol) + ['Medium']
        patch = {'allowedVolatility': new_vol}
        pr = requests.patch(f'{VPS}/api/bot/config/{bot_id}', headers=HEADERS,
                            json=patch, timeout=10)
        print(f'  PATCH -> {pr.status_code}: {pr.text[:200]}')
    else:
        print(f'  Medium already in allowedVolatility, no change needed')
