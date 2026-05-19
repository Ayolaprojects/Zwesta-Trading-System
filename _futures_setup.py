"""
Step 1: See existing credentials and bots.
Step 2: Add a Binance Futures demo credential.
Step 3: Create a futures demo bot.
"""
import urllib.request, json

BASE = 'http://148.113.5.39:9000'

# Login
login = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(BASE + '/api/user/login', data=login, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
H = {'X-Session-Token': token, 'Content-Type': 'application/json'}
HA = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure', 'Content-Type': 'application/json'}

def get(path, hdrs=H):
    req = urllib.request.Request(BASE + path, headers=hdrs)
    return json.loads(urllib.request.urlopen(req, timeout=15).read().decode())

def post(path, body, hdrs=H):
    data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=hdrs)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'detail': e.read().decode()[:300]}

print("="*60)
print("EXISTING CREDENTIALS")
print("="*60)
creds = get('/api/broker/credentials')
for c in creds.get('credentials', []):
    print(f"  {c['credential_id']} | {c.get('label','?')} | server={c.get('server')} | is_live={c.get('is_live')}")

print()
print("="*60)
print("EXISTING BOTS")
print("="*60)
uid = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
bots = get(f'/api/user/{uid}/bots')
for b in bots.get('bots', []):
    print(f"  {b.get('bot_id')} | status={b.get('status')} | broker={b.get('broker_name')} | market={b.get('binanceMarket','spot')} | is_live={b.get('is_live')}")
