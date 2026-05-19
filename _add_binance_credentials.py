"""
Add Binance credentials for:
1. Binance Spot LIVE (is_live=1, server='spot')
2. Binance Futures DEMO (is_live=0, server='futures')
3. Binance Futures LIVE (is_live=1, server='futures')

Usage: Edit the API keys below and run.
"""
import urllib.request, json

base = 'http://148.113.5.39:9000'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

def add_cred(label, api_key, api_secret, server, is_live):
    body = json.dumps({
        'broker_name': 'Binance',
        'account_number': f'BINANCE-{server.upper()}-{"LIVE" if is_live else "DEMO"}',
        'api_key': api_key,
        'password': api_secret,
        'server': server,       # 'spot' or 'futures'
        'is_live': is_live,     # True = real money, False = demo
        'label': label,
    }).encode()
    req = urllib.request.Request(
        base + f'/api/user/{user_id}/broker-credentials',
        data=body, headers=headers
    )
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        r = json.loads(resp.read().decode())
        print(f'  {label}: {r.get("message", r.get("success", r))}')
    except urllib.error.HTTPError as e:
        print(f'  {label}: ERROR {e.code} — {e.read().decode()[:200]}')
    except Exception as e:
        print(f'  {label}: ERROR {e}')

# ============================================================
# FILL IN YOUR API KEYS BELOW
# For Binance demo/spot  → https://demo.binance.com  (testnet)
# For Binance live/spot  → https://www.binance.com/en/my/settings/api-management
# For Binance futures    → same API key works for both spot and futures
#                          just set server='futures'
# ============================================================

# --- DEMO FUTURES (uses same demo API key as spot demo) ---
# Uncomment and fill in if you want a futures demo bot
# add_cred(
#     label='Binance Futures Demo',
#     api_key='YOUR_DEMO_API_KEY',
#     api_secret='YOUR_DEMO_API_SECRET',
#     server='futures',
#     is_live=False,
# )

# --- LIVE SPOT (real money) ---
# add_cred(
#     label='Binance Spot Live',
#     api_key='YOUR_LIVE_API_KEY',
#     api_secret='YOUR_LIVE_API_SECRET',
#     server='spot',
#     is_live=True,
# )

# --- LIVE FUTURES (real money) ---
# add_cred(
#     label='Binance Futures Live',
#     api_key='YOUR_LIVE_API_KEY',
#     api_secret='YOUR_LIVE_API_SECRET',
#     server='futures',
#     is_live=True,
# )

print("Edit this script with your API keys, then uncomment the add_cred() calls.")
print()
print("Current credentials:")
req = urllib.request.Request(base + f'/api/user/{user_id}/broker-credentials', headers=headers)
try:
    creds = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    for c in creds.get('credentials', []):
        print(f"  {c.get('label','?')} | broker={c.get('broker_name')} | server={c.get('server')} | is_live={c.get('is_live')} | active={c.get('is_active')}")
except Exception as e:
    print(f'  (could not list: {e})')
