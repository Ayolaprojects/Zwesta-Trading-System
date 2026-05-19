"""
Check Binance bot trade history to diagnose recovery mode.
"""
import requests, json

VPS = 'http://148.113.5.39:9000'
response = requests.post(f'{VPS}/api/user/login', 
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=15)
TOKEN = response.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}

for bot_id in ['bot_1778970971191', 'bot_1778971251604']:
    r = requests.get(f'{VPS}/api/bot/config/' + bot_id, headers=HEADERS, timeout=10)
    cfg = r.json().get('config', {})
    trades = cfg.get('tradeHistory', [])
    print(bot_id)
    print('  tradeHistory count:', len(trades))
    if trades:
        recent = trades[-6:]
        for t in recent:
            profit = t.get('profit')
            sym = t.get('symbol')
            closed = str(t.get('closedAt', ''))[:19]
            print(f'    profit={profit}, symbol={sym}, closed={closed}')
    
    print('  managementState:', cfg.get('managementState'))
    print('  managementProfile:', cfg.get('managementProfile'))
    print('  effectiveAllowedVolatility:', cfg.get('effectiveAllowedVolatility'))
    print()
