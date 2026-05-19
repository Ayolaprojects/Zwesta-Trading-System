import requests, json, urllib.parse

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
SH = {'X-Session-Token': token}

for bid in ['AZE BOT', 'bot_1779197221415']:
    encoded = urllib.parse.quote(bid, safe='')
    r = requests.get(f'{BASE}/api/bot/config/{encoded}', headers=SH, timeout=10)
    print(f'\n=== {bid} ({r.status_code}) ===')
    if r.ok:
        cfg = r.json().get('bot', r.json())
        keys = [
            'tradeAmount','effectiveTradeAmount','effectivePositionSizeMultiplier',
            'effectiveScannerCapitalMultiplier','signalThreshold','effectiveSignalThreshold',
            'managementState','managementProfile','binanceMarket','binanceFuturesBaseLeverage',
            'effectiveBinanceFuturesLeverage','binanceFuturesMarginType',
            'accountBalance','riskPerTrade','maxDailyLoss','symbols','selectedPreset',
            'lastSizingAdjustment','tradeAmountAdaptation','drawdownPauseUntil',
            'totalTrades','dailyProfit','brokerType','strategy','mode',
            'scannerCapitalLiveMaxBoost','basePositionSize','maxOpenPositions',
        ]
        print(json.dumps({k: cfg.get(k) for k in keys}, indent=2))
    else:
        print(r.text[:200])
