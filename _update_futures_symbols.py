import requests, sqlite3, json, math
from datetime import datetime, timezone

# Step 1: validate ALL candidates against live Binance lot filters
candidates = [
    # Majors
    'SOLUSDT','XRPUSDT','ADAUSDT','BNBUSDT','DOGEUSDT','DOTUSDT','AVAXUSDT',
    # Layer 1s
    'NEARUSDT','ATOMUSDT','APTUSDT','SUIUSDT','INJUSDT','SEIUSDT','TIAUSDT',
    'TONUSDT','HBARUSDT','TRXUSDT','XLMUSDT','ALGOUSDT','VETUSDT',
    # Layer 2s
    'OPUSDT','ARBUSDT','STRKUSDT','ZKUSDT','MANTAUSDT','TAIKOUSDT',
    # DeFi
    'UNIUSDT','AAVEUSDT','ENAUSDT','JUPUSDT','RUNEUSDT','GMXUSDT','CRVUSDT',
    # AI/Infra
    'RENDERUSDT','FETUSDT','NEARUSDT',
    # Storage/Chain
    'FILUSDT','ARUSDT','LDOUSDT',
    # Other quality
    'ONDOUSDT','PYTHUSDT','ZROUSDT','ORDIUSDT','KASUSDT','THETAUSDT',
]
# deduplicate
candidates = list(dict.fromkeys(candidates))

r = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo', timeout=15)
info = r.json()
active = {s['symbol'] for s in info.get('symbols', [])
          if s.get('contractType') == 'PERPETUAL' and s.get('status') == 'TRADING'}
filters_map = {s['symbol']: {f['filterType']: f for f in s.get('filters', [])}
               for s in info.get('symbols', [])}

prices_r = requests.get('https://fapi.binance.com/fapi/v1/ticker/price', timeout=10)
prices = {p['symbol']: float(p['price']) for p in prices_r.json()}

NOTIONAL = 10.87  # 1.087 USDT × 10x leverage

viable = []
skipped = []
for sym in candidates:
    if sym not in active:
        skipped.append((sym, 'not active'))
        continue
    f = filters_map.get(sym, {})
    lot = f.get('LOT_SIZE', {})
    notional_f = f.get('MIN_NOTIONAL', {})
    min_qty = float(lot.get('minQty', 0))
    step = float(lot.get('stepSize', 0) or min_qty)
    min_notional = float(notional_f.get('notional', 5))
    px = prices.get(sym, 0)
    if px <= 0:
        skipped.append((sym, 'no price'))
        continue
    raw_qty = NOTIONAL / px
    qty = math.floor(raw_qty / step) * step if step > 0 else raw_qty
    if qty >= min_qty and NOTIONAL >= min_notional:
        viable.append(sym)
    else:
        skipped.append((sym, f'qty {qty:.5f}<{min_qty} or notional {NOTIONAL}<{min_notional}'))

print(f"Viable: {len(viable)}")
for s in viable:
    print(f"  {s}")
print(f"\nSkipped: {len(skipped)}")
for s, r in skipped:
    print(f"  {s}: {r}")

# Step 2: push to DB + in-memory
BOT_ID = 'bot_1779131132692_3d47eb9b'
BASE = 'http://148.113.5.39:9000'
KEY = 'zwesta_live_api_key_2026_secure'
symbols_str = ','.join(viable)

conn = sqlite3.connect('C:/backend/zwesta_trading.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
now = datetime.now(timezone.utc).isoformat()
cur.execute("UPDATE user_bots SET symbols=?, updated_at=? WHERE bot_id=?", (symbols_str, now, BOT_ID))
cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id=?", (BOT_ID,))
row = cur.fetchone()
if row and row['runtime_state']:
    rs = json.loads(row['runtime_state'])
    rs['symbols'] = viable
    cur.execute("UPDATE user_bots SET runtime_state=? WHERE bot_id=?", (json.dumps(rs), BOT_ID))
conn.commit()
conn.close()
print(f"\nDB updated with {len(viable)} symbols")

headers = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}
r2 = requests.post(f'{BASE}/api/admin/fix-bot-link', headers=headers,
    json={'bot_id': BOT_ID, 'runtime_state': {'symbols': viable}})
print(f"fix-bot-link: {r2.status_code} {r2.text[:150]}")
