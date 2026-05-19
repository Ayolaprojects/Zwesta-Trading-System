import urllib.request, json

base = 'http://148.113.5.39:9000'
login_data = json.dumps({'email':'zwexman@gmail.com','password':'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type':'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token}
bot_id = 'bot_1778970971191'

# Get open positions
print("=== OPEN POSITIONS ===")
req = urllib.request.Request(base + '/api/bot/positions/' + bot_id, headers=headers)
try:
    pos = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    p_list = pos if isinstance(pos, list) else pos.get('positions', [])
    if not p_list:
        print("No open positions")
    for p in p_list:
        sym = p.get('symbol','?')
        side = p.get('side','?')
        qty = p.get('quantity', p.get('qty', 0))
        entry = p.get('entryPrice', p.get('entry_price', 0))
        unrealized = p.get('unrealizedPnl', p.get('pnl', 0))
        print(f"  {sym} {side} qty={qty} entry={entry} unrealized={unrealized}")
except Exception as e:
    print('positions err:', e)

# Get recent trades
print("\n=== RECENT TRADES (last 30) ===")
req = urllib.request.Request(base + '/api/bot/trades/' + bot_id + '?limit=30', headers=headers)
try:
    trades = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    t_list = trades if isinstance(trades, list) else trades.get('trades', [])
    wins = sum(1 for t in t_list if float(t.get('profit', 0)) > 0)
    losses = sum(1 for t in t_list if float(t.get('profit', 0)) < 0)
    zeros = sum(1 for t in t_list if float(t.get('profit', 0)) == 0)
    total_pnl = sum(float(t.get('profit', 0)) for t in t_list)
    print(f"Wins={wins}, Losses={losses}, Zero={zeros}, Total PnL={total_pnl:.2f}")
    print("Recent trades:")
    for t in t_list[:20]:
        sym = t.get('symbol','?')
        side = t.get('side','?')
        pnl = float(t.get('profit', 0))
        status = t.get('status','?')
        close_reason = t.get('closeReason', t.get('close_reason',''))
        print(f"  {sym} {side} pnl={pnl:.2f} status={status} reason={close_reason}")
except Exception as e:
    print('trades err:', e)

# Check scanner status
print("\n=== SCANNER STATUS ===")
req = urllib.request.Request(base + '/api/bots/scanner/' + bot_id + '/status', headers=headers)
try:
    scanner = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    print(json.dumps(scanner, indent=2)[:1500])
except Exception as e:
    print('scanner err:', e)
