"""
Retry stop with long timeout, then PATCH config, then restart.
"""
import urllib.request, json, time

base = 'http://148.113.5.39:9000'
bot_id = 'bot_1778970971191'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

def do(method, path, body=None, timeout=15):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {'error': e.code, 'msg': e.read().decode()[:300]}
    except Exception as e:
        return {'error': str(e)}

# Retry stop up to 5 times
for attempt in range(1, 6):
    print(f"Stop attempt {attempt}...")
    r = do('POST', f'/api/bot/stop/{bot_id}', {'user_id': user_id}, timeout=40)
    msg = r.get('message', '')
    if 'stopped' in str(msg).lower() or r.get('success'):
        print(f"  Stopped: {msg}")
        break
    elif r.get('error') == 409 or 'already' in str(r).lower():
        print("  Bot already stopped, continuing...")
        break
    else:
        print(f"  Result: {r}")
        print(f"  Waiting 10s before retry...")
        time.sleep(10)

time.sleep(5)  # Give the bot time to fully settle

# Try PATCH with 70s timeout
print("\nPatching config with 70s timeout...")
t0 = time.time()
r = do('PATCH', f'/api/bot/config/{bot_id}', {
    'credentialId': 'e568ec38-cfc7-4b05-8033-b56ecdf304e4',
    'tradeAmount': 3500,
    'riskPerTrade': 230,
    'maxDailyLoss': 920,
}, timeout=70)
elapsed = time.time() - t0
print(f"  ({elapsed:.1f}s) Result:", json.dumps(r, indent=2)[:500])

time.sleep(3)

# Restart
print("\nRestarting bot...")
r = do('POST', '/api/bot/start', {'botId': bot_id, 'userId': user_id}, timeout=30)
print(" ", r.get('message', r))

time.sleep(4)

# Verify
print("\nVerifying config:")
r = do('GET', f'/api/bot/config/{bot_id}')
cfg = r.get('config', {})
print(f"  tradeAmount: {cfg.get('tradeAmount')}")
print(f"  riskPerTrade: {cfg.get('riskPerTrade')}")
print(f"  effectiveTradeAmount: {cfg.get('effectiveTradeAmount')}")
adapt = cfg.get('tradeAmountAdaptation') or {}
if adapt:
    print(f"  adaptation.state: {adapt.get('state')}")
    print(f"  adaptation.adjustedTradeAmount: {adapt.get('adjustedTradeAmount')}")
