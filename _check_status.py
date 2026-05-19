import requests

BASE = 'http://148.113.5.39:9000'
s = requests.post(BASE + '/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=20)
token = s.json().get('session_token','')
h = {'X-Session-Token': token}
r = requests.get(BASE + '/api/bot/status', headers=h, timeout=15)
bots = r.json() if isinstance(r.json(), list) else r.json().get('bots', [])
print(f'Total bots: {len(bots)}')
for b in bots:
    bid = b.get('botId')
    broker = b.get('broker_type','')
    status = b.get('status')
    enabled = b.get('enabled')
    acct = b.get('accountId','')
    balance = b.get('accountBalance')
    positions = b.get('openPositions') or []
    print(f'  {bid}: {broker} | {status} | enabled={enabled}')
    print(f'    acct={acct} | balance={balance}')
    for pos in positions:
        print(f'    POS: {pos.get("symbol")} {pos.get("type")} qty={pos.get("quantity")} profit={pos.get("profit")}')
