"""Use PATCH /api/bot/config/<bot_id> to reset trade amount."""
import urllib.request, json

base = 'http://148.113.5.39:9000'
bot_id = 'bot_1778970971191'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

# First GET to see current config
req = urllib.request.Request(base + f'/api/bot/config/{bot_id}', headers=headers)
config = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
print("Current config keys:", list(config.get('config', {}).keys()))
print("tradeAmount:", config['config'].get('tradeAmount'))
print("riskPerTrade:", config['config'].get('riskPerTrade'))
print("maxDailyLoss:", config['config'].get('maxDailyLoss'))
print("positionSizeMultiplier:", config['config'].get('positionSizeMultiplier'))
print("tradeAmountAdaptation:", config['config'].get('tradeAmountAdaptation'))

# Now PATCH with reduced amounts
patch_data = json.dumps({
    'tradeAmount': 3500,
    'riskPerTrade': 230,
    'maxDailyLoss': 920,
}).encode()
req = urllib.request.Request(
    base + f'/api/bot/config/{bot_id}',
    data=patch_data,
    headers=headers,
    method='PATCH'
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read().decode())
    print("\nPATCH result:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"\nPATCH error {e.code}: {e.read().decode()[:500]}")
except Exception as e:
    print(f"\nPATCH error: {e}")
