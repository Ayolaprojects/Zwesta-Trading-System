import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}

r = requests.get(f'{BASE}/api/bot/status', headers=SH, timeout=10)
data = r.json()
bots = data.get('bots', [])
print(f"Total bots: {len(bots)}")
for b in bots:
    bid = b.get('botId','')
    broker = b.get('brokerName','') or ''
    enabled = b.get('enabled')
    ta = b.get('tradeAmount')
    eta = b.get('effectiveTradeAmount')
    print(f"  {bid} | {broker} | enabled={enabled} | tradeAmount={ta} | effectiveTradeAmount={eta}")
