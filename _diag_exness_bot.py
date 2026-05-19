import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}

r = requests.get(f'{BASE}/api/bot/status', headers=SH, timeout=10)
bots = r.json().get('bots', [])

for b in bots:
    bid = b.get('botId','')
    broker = b.get('brokerName','')
    if 'Exness' in broker or 'exness' in broker.lower() or '1779112' in bid:
        print(f"=== BOT: {bid} ===")
        for k in ['name','brokerName','enabled','status','tradeAmount','effectiveTradeAmount',
                  'managementProfile','managementMode','tradeAmountAdaptation',
                  'drawdownPauseUntil','totalProfit','dailyProfit','accountBalance']:
            print(f"  {k}: {b.get(k)}")

# Also get detailed config
for b in bots:
    bid = b.get('botId','')
    broker = b.get('brokerName','')
    if 'Exness' in broker or 'exness' in broker.lower() or '1779112' in bid:
        r2 = requests.get(f'{BASE}/api/bot/config/{requests.utils.quote(bid)}', headers=SH, timeout=10)
        cfg = r2.json().get('config', {})
        print(f"\n=== CONFIG for {bid} ===")
        for k in ['tradeAmount','effectiveTradeAmount','tradeAmountAdaptation',
                  'dailyProfitPeaks','managementProfile','intelligentScanner',
                  'allowedVolatility','signalThreshold','riskPerTrade',
                  'maxDailyLoss','drawdownPauseUntil','symbols']:
            print(f"  {k}: {json.dumps(cfg.get(k))[:200]}")
