"""
Create a Binance Futures DEMO bot using the new futures credential.
"""
import urllib.request, json

BASE = 'http://148.113.5.39:9000'
FUTURES_CRED_ID = '5fe101ac-dcb5-4d3f-85f3-f4b23f03a31c'

# Login
login = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(BASE + '/api/user/login', data=login, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
H = {'X-Session-Token': token, 'Content-Type': 'application/json'}

# Check the credential is visible via API
print("Credentials via API:")
req = urllib.request.Request(BASE + '/api/broker/credentials', headers=H)
creds = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
for c in creds.get('credentials', []):
    print(f"  {c['credential_id']} | {c.get('label','?')} | server={c.get('server')} | is_live={c.get('is_live')}")

# Create the futures bot
print("\nCreating Binance Futures DEMO bot...")
body = json.dumps({
    'credentialId': FUTURES_CRED_ID,
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'tradeAmount': 50,
    'strategy': 'adaptive',
    'binanceMarket': 'futures',
}).encode()
req = urllib.request.Request(BASE + '/api/bot/create', data=body, headers=H)
try:
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    print("Result:", json.dumps(r, indent=2))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()[:400]}")
except Exception as e:
    print(f"Timeout/Error: {e}")
