"""Get the full VPS bot config to understand what's driving the volatility restriction."""
import requests, json

VPS = 'http://148.113.5.39:9000'
response = requests.post(f'{VPS}/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
data = response.json()
TOKEN = data['session_token']
HEADERS = {'X-Session-Token': TOKEN}

r = requests.get(f'{VPS}/api/bot/config/bot_1778970971191', headers=HEADERS, timeout=15)
cfg = r.json().get('config', {})

keys_of_interest = [
    'managementMode', 'managementProfile', 'managementState',
    'allowedVolatility', 'effectiveAllowedVolatility',
    'signalThreshold', 'effectiveSignalThreshold',
    'signalThresholdMode', 'enabled',
]

print('=== bot_1778970971191 config ===')
for k in keys_of_interest:
    print(f'  {k}: {cfg.get(k)}')

recent_trades = (cfg.get('tradeHistory') or [])[-6:]
print(f'\n  tradeHistory (last 6):')
for t in recent_trades:
    print(f'    profit={t.get("profit")}, symbol={t.get("symbol")}, closed={str(t.get("closedAt",""))[:19]}')

print(f'\n  All config keys ({len(cfg)}):')
for k in sorted(cfg.keys()):
    v = cfg[k]
    if not isinstance(v, (dict, list)) or k in ('allowedVolatility', 'effectiveAllowedVolatility'):
        print(f'    {k}: {v}')
