import requests, json
BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}

for bot_id in ['bot_1779185407301', 'bot_1779197221415', 'bot_1779201336253', 'AZE BOT']:
    r = requests.get(f'{BASE}/api/bot/config/{requests.utils.quote(bot_id)}', headers=SH, timeout=10)
    cfg = r.json().get('config', {})
    adapt = cfg.get('tradeAmountAdaptation') or {}
    broker = cfg.get('brokerName','')
    print(f"\n=== {bot_id} ({broker}) ===")
    print(f"  enabled:               {cfg.get('enabled')}")
    print(f"  tradeAmount:           {cfg.get('tradeAmount')}")
    print(f"  effectiveTradeAmount:  {cfg.get('effectiveTradeAmount')}")
    print(f"  PSM:                   {cfg.get('effectivePositionSizeMultiplier')}")
    print(f"  intelligentScanner:    {cfg.get('intelligentScanner')}")
    print(f"  allowedVolatility:     {cfg.get('allowedVolatility')}")
    print(f"  drawdownPauseUntil:    {cfg.get('drawdownPauseUntil')}")
    print(f"  managementProfile:     {cfg.get('managementProfile')}")
    if adapt:
        print(f"  adaptation.state:      {adapt.get('state')}")
        print(f"  adaptation.multiplier: {adapt.get('multiplier')}")
        print(f"  adaptation.reason:     {adapt.get('reason','')[:80]}")
        print(f"  adaptation.dailyProfit:{adapt.get('dailyProfit')}")
