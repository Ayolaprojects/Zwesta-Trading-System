import requests, json
VPS = 'http://148.113.5.39:9000'
r = requests.post(f'{VPS}/api/user/login', json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
T = r.json()['session_token']
H = {'X-Session-Token': T}

for bot_id in ['bot_1778970971191', 'bot_1778971251604']:
    r2 = requests.get(f'{VPS}/api/bot/config/{bot_id}', headers=H, timeout=15)
    cfg = r2.json().get('config', {})
    print(f'{bot_id}:')
    mgmt_mode = cfg.get('managementMode')
    mgmt_profile = cfg.get('managementProfile')
    av = cfg.get('allowedVolatility')
    eav = cfg.get('effectiveAllowedVolatility')
    enabled = cfg.get('enabled')
    ops = cfg.get('open_positions') or cfg.get('openPositions') or []
    print(f'  managementMode: {mgmt_mode}')
    print(f'  managementProfile: {mgmt_profile}')
    print(f'  allowedVolatility: {av}')
    print(f'  effectiveAllowedVolatility: {eav}')
    print(f'  enabled: {enabled}')
    print(f'  open_positions count: {len(ops) if isinstance(ops, list) else ops}')
    print()
