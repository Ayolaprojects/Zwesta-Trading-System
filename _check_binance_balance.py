"""
Decrypt Binance credentials and check actual free USDT balance.
Also check open orders on Binance demo.
"""
import sys, sqlite3, json, hmac, hashlib, time
sys.path.insert(0, r'C:\backend')
from credential_crypto import decrypt_secret

db = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db)
row = conn.execute(
    'SELECT api_key, password FROM broker_credentials WHERE credential_id=?',
    ('e568ec38-cfc7-4b05-8033-b56ecdf304e4',)
).fetchone()
conn.close()

api_key = decrypt_secret(row[0])
api_secret = decrypt_secret(row[1])
print(f'API key: {api_key[:8]}...')
print(f'API secret len: {len(api_secret)}')

# Make signed request to Binance demo
import urllib.request, urllib.parse, requests as _req

base = 'https://demo-api.binance.com/api'

def signed_request(method, path, params=None):
    params = params or {}
    ts = int(time.time() * 1000)
    params['timestamp'] = ts
    query = urllib.parse.urlencode(sorted(params.items()))
    sig = hmac.new(api_secret.encode('utf-8'), query.encode('utf-8'), hashlib.sha256).hexdigest()
    url = f'{base}{path}?{query}&signature={sig}'
    resp = _req.request(method, url, headers={
        'X-MBX-APIKEY': api_key,
        'Content-Type': 'application/json'
    }, timeout=15)
    if not resp.ok:
        print(f'  HTTP {resp.status_code}: {resp.text[:200]}')
        return None
    return resp.json()

# Get account info
print('\n=== BINANCE ACCOUNT ===')
try:
    acct = signed_request('GET', '/v3/account')
    if acct:
        balances = {b['asset']: b for b in acct.get('balances', []) if float(b['free']) > 0 or float(b['locked']) > 0}
        total_usdt = float(balances.get('USDT', {}).get('free', 0))
        locked_usdt = float(balances.get('USDT', {}).get('locked', 0))
        print(f'USDT free: {total_usdt:.2f}')
        print(f'USDT locked: {locked_usdt:.2f}')
        print('All non-zero balances:')
        for asset, b in sorted(balances.items()):
            print(f'  {asset}: free={b["free"]} locked={b["locked"]}')
except Exception as e:
    print(f'Account error: {e}')

# Get open orders
print('\n=== OPEN ORDERS ===')
try:
    orders = signed_request('GET', '/v3/openOrders', {'symbol': 'BTCUSDT'})
    if orders is not None:
        if orders:
            for o in orders:
                print(f'  {o["orderId"]}: {o["side"]} {o["origQty"]} BTC @ {o["price"]} status={o["status"]}')
        else:
            print('  No open orders for BTCUSDT')
except Exception as e:
    print(f'Open orders error: {e}')
