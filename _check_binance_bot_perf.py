import requests, json

BASE = 'http://148.113.5.39:9000'
s = requests.post(BASE + '/api/user/login', json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
h = {'X-Session-Token': token}
ADMIN = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure'}

BINANCE_BOTS = [
    'bot_1779029733318_cf548079',
    'bot_1779029679564_b8070b61',
    'bot_1778971251604',
]

for bid in BINANCE_BOTS:
    cfg = requests.get(BASE + '/api/bot/config/' + bid, headers=h, timeout=20).json()
    b = cfg.get('bot', cfg.get('config', cfg))

    # try performance endpoint
    perf = requests.get(BASE + '/api/bot/' + bid + '/performance', headers=h, timeout=20)
    pdata = perf.json() if perf.status_code == 200 else {}

    # try trades endpoint
    trades = requests.get(BASE + '/api/bot/' + bid + '/trades?limit=20', headers=h, timeout=20)
    tdata = trades.json() if trades.status_code == 200 else {}
    tlist = tdata if isinstance(tdata, list) else tdata.get('trades', [])

    total_pnl = sum(float(t.get('profit', t.get('pnl', 0)) or 0) for t in tlist)
    wins = sum(1 for t in tlist if float(t.get('profit', t.get('pnl', 0)) or 0) > 0)
    losses = sum(1 for t in tlist if float(t.get('profit', t.get('pnl', 0)) or 0) < 0)

    print(f'\n=== {bid} ===')
    print(f'  name:        {b.get("name")}')
    print(f'  strategy:    {b.get("strategy")}')
    print(f'  symbols:     {b.get("symbols")}')
    print(f'  enabled:     {b.get("enabled")}')
    print(f'  tradeAmount: {b.get("tradeAmount")}')
    print(f'  daily_profit:{b.get("daily_profit", b.get("dailyProfit", "?"))}')
    print(f'  total_profit:{b.get("total_profit", b.get("totalProfit", "?"))}')
    print(f'  trades last20: {len(tlist)} | wins={wins} losses={losses} | pnl={total_pnl:.4f}')
    if pdata:
        print(f'  perf data:   {json.dumps(pdata)[:200]}')
