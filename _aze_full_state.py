import requests, json
BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}
r = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r.json().get('config', {})
print('enabled:', cfg.get('enabled'))
print('tradeAmount:', cfg.get('tradeAmount'))
print('effectiveTradeAmount:', cfg.get('effectiveTradeAmount'))
print('dailyProfitPeaks:', cfg.get('dailyProfitPeaks'))
print('tradeAmountAdaptation:', json.dumps(cfg.get('tradeAmountAdaptation'), indent=2)[:400])
