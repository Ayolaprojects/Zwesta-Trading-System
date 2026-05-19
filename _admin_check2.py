import requests, json
VPS = 'http://148.113.5.39:9000'
API_KEY = 'zwesta_live_api_key_2026_secure'
H = {'Authorization': 'Bearer ' + API_KEY}

for bid in ['bot_1778970971191', 'bot_1778971251604']:
    r = requests.get(f'{VPS}/api/admin/bot-daily-loss-debug', headers=H, params={'bot_id': bid}, timeout=15)
    d = r.json().get('diagnostics', {})
    op = d.get('openPositionCount')
    ct = d.get('closedTradesToday')
    th = d.get('tradeHistoryCount')
    rp = d.get('recentDailyProfits')
    print(f'{bid}: openPositionCount={op}, closedToday={ct}, tradeHistoryCount={th}')
    print(f'  recentDailyProfits={rp}')
