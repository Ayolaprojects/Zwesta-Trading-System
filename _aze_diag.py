import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
SH = {'X-Session-Token': token}
r = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r.json().get('config', {})

print('=== KEY METRICS ===')
print(f"tradeAmount: {cfg.get('tradeAmount')}")
print(f"effectiveTradeAmount: {cfg.get('effectiveTradeAmount')}")
print(f"intelligentScanner: {cfg.get('intelligentScanner')}")
print(f"allowedVolatility: {cfg.get('allowedVolatility')}")
print(f"signalThreshold: {cfg.get('signalThreshold')}")
print(f"signalThresholdMode: {cfg.get('signalThresholdMode')}")
print(f"accountBalance: {cfg.get('accountBalance')}")
print(f"managementProfile: {cfg.get('managementProfile')}")
print(f"PSM: {cfg.get('effectivePositionSizeMultiplier')}")
print(f"SCM: {cfg.get('effectiveScannerCapitalMultiplier')}")

print('\n=== TRADE AMOUNT ADAPTATION ===')
print(json.dumps(cfg.get('tradeAmountAdaptation'), indent=2))

print('\n=== SYMBOL PERFORMANCE ===')
sp = cfg.get('symbolPerformance') or {}
for sym, perf in sp.items():
    v = perf.get('verdict')
    m = perf.get('multiplier')
    pnl = perf.get('pnl')
    s = perf.get('samples')
    wr = perf.get('winRate')
    print(f"  {sym}: verdict={v} mult={m} pnl={pnl} samples={s} winRate={wr}")
