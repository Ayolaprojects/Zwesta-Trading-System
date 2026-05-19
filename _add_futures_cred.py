"""
Add Binance Futures demo credential using the same API key as existing spot demo.
Then create a futures demo bot.
"""
import sys, sqlite3, json, urllib.request
sys.path.insert(0, r'C:\backend')

# ── Decrypt existing Binance spot demo credentials ──────────────────────────
db = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()
row = c.execute(
    "SELECT api_key, password FROM broker_credentials WHERE credential_id=?",
    ('e568ec38-cfc7-4b05-8033-b56ecdf304e4',)
).fetchone()

api_key_enc = row['api_key']
api_secret_enc = row['password']
conn.close()

try:
    from credential_crypto import decrypt_secret
    api_key = decrypt_secret(api_key_enc) if api_key_enc and api_key_enc.startswith('enc:') else api_key_enc
    api_secret = decrypt_secret(api_secret_enc) if api_secret_enc and api_secret_enc.startswith('enc:') else api_secret_enc
    print(f"API key: {api_key[:10]}...")
    print(f"API secret: {api_secret[:6]}...")
except Exception as e:
    print(f"Decrypt error: {e}")
    print("Stored api_key:", api_key_enc[:30] if api_key_enc else None)
    sys.exit(1)

# ── Login ─────────────────────────────────────────────────────────────────────
BASE = 'http://148.113.5.39:9000'
login = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(BASE + '/api/user/login', data=login, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
H = {'X-Session-Token': token, 'Content-Type': 'application/json'}

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'detail': e.read().decode()[:400]}

# ── Add Binance Futures DEMO credential ──────────────────────────────────────
print("\nAdding Binance Futures DEMO credential...")
r = post('/api/broker/credentials', {
    'broker_name': 'Binance',
    'account_number': 'BINANCE-FUTURES-DEMO',
    'api_key': api_key,
    'api_secret': api_secret,
    'server': 'futures',
    'is_live': False,
    'label': 'Binance Futures Demo',
})
print("Result:", json.dumps(r, indent=2))

futures_cred_id = r.get('credential_id') or r.get('credentialId')
if futures_cred_id:
    print(f"\nNew futures credential ID: {futures_cred_id}")
    print("\nCreating Binance Futures DEMO bot...")
    r2 = post('/api/bot/create', {
        'credentialId': futures_cred_id,
        'symbols': ['BTCUSDT', 'ETHUSDT'],
        'tradeAmount': 50,
        'strategy': 'adaptive',
        'binanceMarket': 'futures',
    })
    print("Bot create result:", json.dumps(r2, indent=2))
else:
    print("Could not get credential ID from response.")
