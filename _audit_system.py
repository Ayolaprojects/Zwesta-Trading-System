import requests, json

BASE = 'http://148.113.5.39:9000'
r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
tok = r.json()['session_token']
h = {'X-Session-Token': tok}
HA = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure'}

bot_ids = [
    'bot_1779057251465',
    'bot_1779029733318_cf548079',
    'bot_1779029679564_b8070b61',
    'bot_1778971251604',
    'bot_1778970971191',
    'bot_1778970611374',
    'bot_1779011553325',
]

print("=" * 90)
print("BOT AUDIT")
print("=" * 90)
for bid in bot_ids:
    s = requests.get(f'{BASE}/api/bot/config/{bid}', headers=h, timeout=15)
    if s.status_code != 200:
        print(f"{bid} | HTTP {s.status_code}")
        continue
    resp = s.json()
    cfg = resp.get('config', {})
    pp = cfg.get('profitProtection', {})
    running = resp.get('running', False)
    broker = cfg.get('brokerName', '?')
    market = cfg.get('binanceMarket', '')
    symbols = cfg.get('symbols', [])
    trade_amt = cfg.get('tradeAmount', cfg.get('fixedTradeAmount', '?'))
    cred_id = cfg.get('credentialId', '?')
    bEB = pp.get('breakEvenBufferProfit', '?')
    rCP = pp.get('retraceClosePercent', '?')
    mLP = pp.get('minLockedProfit', '?')
    bAS = pp.get('breakEvenActivationShare', '?')
    print(f"\n{bid}")
    print(f"  broker={broker} market={market} running={running}")
    print(f"  credentialId={cred_id}")
    print(f"  symbols={symbols}")
    print(f"  tradeAmount={trade_amt}")
    print(f"  PP: bEB={bEB} rCP={rCP} mLP={mLP} bAS={bAS}")

print("\n" + "=" * 90)
print("CREDENTIALS")
print("=" * 90)
cr = requests.get(f'{BASE}/api/credentials', headers=h, timeout=15)
print(f"  status={cr.status_code} text={cr.text[:300]}")

# Try admin endpoint
cr2 = requests.get(f'{BASE}/api/admin/credentials', headers=HA, timeout=15)
print(f"  admin status={cr2.status_code} text={cr2.text[:500]}")
