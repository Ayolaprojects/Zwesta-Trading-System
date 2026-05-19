import json

import requests

BASE = 'http://148.113.5.39:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'
BOT_ID = 'bot_1778879535397'

resp = requests.post(
    f'{BASE}/api/user/login',
    json={'email': EMAIL, 'password': PASSWORD},
    timeout=30,
)
resp.raise_for_status()
token = resp.json()['session_token']
headers = {'X-Session-Token': token}
status_payload = requests.get(f'{BASE}/api/bot/status', headers=headers, timeout=30)
status_payload.raise_for_status()
config_payload = requests.get(f'{BASE}/api/bot/config/{BOT_ID}', headers=headers, timeout=30)
config_payload.raise_for_status()

bot = next(
    (item for item in status_payload.json().get('bots', []) if item.get('botId') == BOT_ID),
    None,
)
config = config_payload.json().get('config', {})

print(json.dumps({
    'status': bot.get('status') if bot else None,
    'enabled': bot.get('enabled') if bot else None,
    'openPositions': len(bot.get('openPositions') or []) if bot else None,
    'signalThreshold_status': bot.get('signalThreshold') if bot else None,
    'managementProfile_status': bot.get('managementProfile') if bot else None,
    'signalThreshold_config': config.get('signalThreshold'),
    'managementProfile_config': config.get('managementProfile'),
    'postCloseCooldownMinutes': config.get('postCloseCooldownMinutes'),
    'postLossSameDirectionCooldownMinutes': config.get('postLossSameDirectionCooldownMinutes'),
    'tradeAmount': config.get('tradeAmount'),
    'maxOpenPositions': config.get('maxOpenPositions'),
    'maxPositionsPerSymbol': config.get('maxPositionsPerSymbol'),
}, indent=2))
