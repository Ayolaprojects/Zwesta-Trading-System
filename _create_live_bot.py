"""
Create a LIVE bot (spot or futures) once you have the credential ID from _add_live_binance_creds.py.
Usage:
  python _create_live_bot.py SPOT <credential_id>
  python _create_live_bot.py FUTURES <credential_id>

WARNING: This creates a REAL MONEY bot. Start with a small tradeAmount.
"""
import sys, urllib.request, json

BASE = 'http://148.113.5.39:9000'

if len(sys.argv) < 3:
    print("Usage: python _create_live_bot.py SPOT|FUTURES <credential_id>")
    sys.exit(1)

market = sys.argv[1].lower()   # 'spot' or 'futures'
cred_id = sys.argv[2]

# Login
login = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(BASE + '/api/user/login', data=login, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
H = {'X-Session-Token': token, 'Content-Type': 'application/json'}

print(f"Creating Binance {market.upper()} LIVE bot with credential {cred_id}...")
body = json.dumps({
    'credentialId': cred_id,
    'symbols': ['BTCUSDT', 'ETHUSDT'],
    'tradeAmount': 50,       # <- Start SMALL (e.g. $50 per trade) for live!
    'strategy': 'adaptive',
    'binanceMarket': market,
}).encode()
req = urllib.request.Request(BASE + '/api/bot/create', data=body, headers=H)
try:
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    if r.get('success'):
        print(f"Bot created: {r.get('bot_id', r)}")
    else:
        print(f"Failed: {r}")
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode()[:400]}")
except Exception as e:
    print(f"Timeout/Error: {e}")
