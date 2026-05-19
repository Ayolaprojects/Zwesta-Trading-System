import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}

for bot_id in ['bot_1779185407301', 'bot_1779197221415', 'AZE BOT']:
    r = requests.get(f'{BASE}/api/bot/config/{requests.utils.quote(bot_id)}', headers=SH, timeout=10)
    cfg = r.json().get('config', {})
    broker = cfg.get('brokerName','')
    print(f"\n=== {bot_id} ({broker}) ===")
    adapt = cfg.get('tradeAmountAdaptation') or {}
    print(f"  tradeAmount: {cfg.get('tradeAmount')}")
    print(f"  effectiveTradeAmount: {cfg.get('effectiveTradeAmount')}")
    print(f"  managementProfile: {cfg.get('managementProfile')}")
    print(f"  symbols: {cfg.get('symbols')}")
    print(f"  drawdownPauseUntil: {cfg.get('drawdownPauseUntil')}")
    if adapt:
        print(f"  tradeAmountAdaptation:")
        print(f"    retraceRatio: {adapt.get('retraceRatio')}")
        print(f"    lastPeak: {adapt.get('lastPeak')}")
        print(f"    currentProfit: {adapt.get('currentProfit')}")
        print(f"    state: {adapt.get('state')}")
        print(f"    reason: {adapt.get('reason')}")
    print(f"  lastAdaptationReason: {cfg.get('lastAdaptationReason')}")
    print(f"  effectivePositionSizeMultiplier: {cfg.get('effectivePositionSizeMultiplier')}")
