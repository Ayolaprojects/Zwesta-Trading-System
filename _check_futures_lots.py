import requests

# Pull ALL active USDT-margined futures pairs
r = requests.get('https://fapi.binance.com/fapi/v1/exchangeInfo', timeout=15)
info = r.json()

prices_r = requests.get('https://fapi.binance.com/fapi/v1/ticker/price', timeout=10)
prices = {p['symbol']: float(p['price']) for p in prices_r.json()}

notional_budget = 10.87  # 1.087 USDT margin × 10x leverage

ok_symbols = []
fail_symbols = []

for s in info.get('symbols', []):
    sym = s['symbol']
    if not sym.endswith('USDT'):
        continue
    if s.get('contractType') != 'PERPETUAL':
        continue
    if s.get('status') != 'TRADING':
        continue

    filters = {f['filterType']: f for f in s.get('filters', [])}
    lot = filters.get('LOT_SIZE', {})
    notional_f = filters.get('MIN_NOTIONAL', {})

    min_qty = float(lot.get('minQty', 0))
    step_size = float(lot.get('stepSize', 0))
    min_notional = float(notional_f.get('notional', 5))

    px = prices.get(sym, 0)
    if px <= 0:
        continue

    our_qty = notional_budget / px
    # round down to step size
    if step_size > 0:
        import math
        our_qty = math.floor(our_qty / step_size) * step_size

    ok = our_qty >= min_qty and notional_budget >= min_notional
    if ok:
        ok_symbols.append(sym)
    else:
        fail_symbols.append((sym, round(min_qty, 6), round(px, 4), round(min_notional, 1), round(our_qty, 6)))

print(f"\n=== OK ({len(ok_symbols)} symbols) ===")
for s in sorted(ok_symbols):
    print(f"  {s}")

print(f"\n=== FAIL ({len(fail_symbols)} symbols, first 10) ===")
for row in sorted(fail_symbols, key=lambda x: x[0])[:10]:
    print(f"  {row[0]:<14} minQty={row[1]} price={row[2]} minNotional={row[3]} ourQty={row[4]}")

