import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token') or d.get('token','')
uid = d.get('user_id','8e74db37-fd1e-4c57-87c4-ad3b64012ecf')
SH = {'X-Session-Token': token}

# list bots
r = requests.get(f'{BASE}/api/user/{uid}/bots', headers=SH, timeout=10)
bots = r.json().get('bots', [])
print(f'Found {len(bots)} bots')

for b in bots:
    bot_id = b.get('bot_id','')
    print(f'\n--- {bot_id} | {b.get("name")} ---')
    r2 = requests.get(f'{BASE}/api/user/{uid}/bot/{bot_id}', headers=SH, timeout=10)
    if r2.ok:
        cfg = r2.json().get('bot', r2.json())
        print(json.dumps({
            'tradeAmount': cfg.get('tradeAmount'),
            'effectiveTradeAmount': cfg.get('effectiveTradeAmount'),
            'effectivePositionSizeMultiplier': cfg.get('effectivePositionSizeMultiplier'),
            'effectiveScannerCapitalMultiplier': cfg.get('effectiveScannerCapitalMultiplier'),
            'signalThreshold': cfg.get('signalThreshold'),
            'effectiveSignalThreshold': cfg.get('effectiveSignalThreshold'),
            'managementState': cfg.get('managementState'),
            'managementProfile': cfg.get('managementProfile'),
            'binanceMarket': cfg.get('binanceMarket'),
            'binanceFuturesBaseLeverage': cfg.get('binanceFuturesBaseLeverage'),
            'effectiveBinanceFuturesLeverage': cfg.get('effectiveBinanceFuturesLeverage'),
            'binanceFuturesMarginType': cfg.get('binanceFuturesMarginType'),
            'accountBalance': cfg.get('accountBalance'),
            'basePositionSize': cfg.get('basePositionSize'),
            'riskPerTrade': cfg.get('riskPerTrade'),
            'maxDailyLoss': cfg.get('maxDailyLoss'),
            'maxOpenPositions': cfg.get('maxOpenPositions'),
            'dailyProfit': cfg.get('dailyProfit'),
            'totalProfit': cfg.get('totalProfit'),
            'totalTrades': cfg.get('totalTrades'),
            'drawdownPauseUntil': cfg.get('drawdownPauseUntil'),
            'lastSizingAdjustment': cfg.get('lastSizingAdjustment'),
            'tradeAmountAdaptation': cfg.get('tradeAmountAdaptation'),
            'symbols': cfg.get('symbols'),
            'selectedPreset': cfg.get('selectedPreset'),
            'scannerCapitalLiveMaxBoost': cfg.get('scannerCapitalLiveMaxBoost'),
            'adaptiveSignalThresholdOffset': cfg.get('adaptiveSignalThresholdOffset'),
            'brokerType': cfg.get('brokerType'),
        }, indent=2))
    else:
        print(r2.status_code, r2.text[:200])

