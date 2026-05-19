"""
Create a new bot using an existing credential.
After adding credentials with _add_binance_credentials.py, run this to create bots.
"""
import urllib.request, json

base = 'http://148.113.5.39:9000'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

# Step 1: List all credentials so you can pick the ID
print("=== Available Credentials ===")
req = urllib.request.Request(base + f'/api/user/{user_id}/broker-credentials', headers=headers)
creds = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
for c in creds.get('credentials', []):
    print(f"  {c.get('credential_id')} | {c.get('label','?')} | server={c.get('server')} | is_live={c.get('is_live')}")

# Step 2: List existing bots
print("\n=== Existing Bots ===")
req = urllib.request.Request(base + f'/api/user/{user_id}/bots', headers=headers)
bots = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
for b in bots.get('bots', []):
    print(f"  {b.get('bot_id')} | {b.get('name','?')} | status={b.get('status')} | broker={b.get('broker_name')} | market={b.get('binanceMarket','spot')} | live={b.get('is_live')}")

# Step 3: Create a bot — fill in credential_id from above
# ============================================================
# CONFIGURATION
CREDENTIAL_ID = 'PASTE_CREDENTIAL_ID_HERE'   # <- from step 1
BOT_SYMBOLS = ['BTCUSDT', 'ETHUSDT']
TRADE_AMOUNT = 50    # USD per trade (start small!)
BINANCE_MARKET = 'futures'   # 'spot' or 'futures'
# ============================================================

if CREDENTIAL_ID != 'PASTE_CREDENTIAL_ID_HERE':
    body = json.dumps({
        'credentialId': CREDENTIAL_ID,
        'symbols': BOT_SYMBOLS,
        'tradeAmount': TRADE_AMOUNT,
        'strategy': 'adaptive',
        'binanceMarket': BINANCE_MARKET,
    }).encode()
    req = urllib.request.Request(
        base + '/api/bot/create',
        data=body, headers=headers
    )
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
        print(f"\nBot created: {r}")
    except urllib.error.HTTPError as e:
        print(f"\nCreate error {e.code}: {e.read().decode()[:400]}")
else:
    print("\n(Edit CREDENTIAL_ID above and re-run to create a bot)")
