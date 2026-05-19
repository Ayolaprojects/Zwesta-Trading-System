import requests, json, time

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
SH = {'X-Session-Token': token}

# Fetch current config
r = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r.json().get('config', {})
print(f"Current: tradeAmount={cfg.get('tradeAmount')} effectiveTradeAmount={cfg.get('effectiveTradeAmount')}")

patch = {
    'credentialId': cfg.get('credentialId'),
    'tradeAmount': 20.0,
    'intelligentScanner': True,
    'allowedVolatility': ['Low', 'Medium', 'High'],
    'tradeAmountAdaptation': None,
    'dailyProfitPeaks': {},
    'effectiveTradeAmount': None,
    'symbols': cfg.get('symbols'),
    'strategy': cfg.get('strategy'),
    'signalThreshold': cfg.get('signalThreshold'),
    'managementProfile': cfg.get('managementProfile'),
    'maxDailyLoss': cfg.get('maxDailyLoss'),
    'maxOpenPositions': cfg.get('maxOpenPositions'),
    'riskPerTrade': cfg.get('riskPerTrade'),
}

print('Patching (60s timeout)...')
r2 = requests.put(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, json=patch, timeout=60)
print(f'Patch: {r2.status_code}')
print(r2.text[:500])
