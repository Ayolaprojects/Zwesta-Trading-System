"""
Use update_bot_config API to reset effective trade amount in active_bots (in-memory).
This does NOT trigger BinanceConnection.connect(), so no timeout.
"""
import urllib.request, json, time

base = 'http://148.113.5.39:9000'
bot_id = 'bot_1778970971191'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json', 'Authorization': 'Bearer zwesta_live_api_key_2026_secure'}

# Check current bot state first
def get(path):
    req = urllib.request.Request(base + path, headers=headers)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
    except Exception as e:
        return {'error': str(e)}

def post(path, body, timeout=20):
    data = json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'msg': e.read().decode()}
    except Exception as e:
        return {'error': str(e)}

# Check current active bot status
bots = get('/api/bots')
if 'bots' in bots:
    for b in bots['bots']:
        if b['bot_id'] == bot_id:
            print(f"Current bot status: {b.get('status')}")
            print(f"  effectiveTradeAmount: {b.get('effectiveTradeAmount')}")
            print(f"  riskPerTrade: {b.get('riskPerTrade')}")

# Try PATCH with config override
print("\nAttempting config update...")
result = post('/api/bot/update_config/' + bot_id, {
    'userId': user_id,
    'riskPerTrade': 230,
    'maxDailyLoss': 920,
    'effectiveTradeAmount': 3500,
    'effectivePositionSizeMultiplier': 1.0,
    'effectiveScannerCapitalMultiplier': 1.0,
    'tradeAmountAdaptationState': 'normal',
    'tradeAmountAdaptationMultiplier': 1.0,
}, timeout=35)
print("Result:", json.dumps(result, indent=2))
