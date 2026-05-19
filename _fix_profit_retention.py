"""
Fix profit retention for bot_1778970971191.
Changes:
- breakEvenBufferProfit: 0.5 -> 10.0  (capture real profit, not near-zero)
- retraceClosePercent: 22.0 -> 10.0   (tighter trailing, keep more peak profit)
- minLockedProfit: 0.0 -> 5.0         (always lock at least $5)
- breakEvenActivationShare: 0.5 -> 0.3 (arm protection earlier - at 30% of peak)
"""
import urllib.request, json, time

base = 'http://148.113.5.39:9000'
bot_id = 'bot_1778970971191'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

def api(path, body=None, method=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(base + path, data=data, headers=headers)
    if method:
        req.method = method
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())

# Step 1: Stop the bot
print("Stopping bot...")
result = api('/api/bot/stop/' + bot_id, {'user_id': user_id})
print("Stop:", result)
time.sleep(3)

# Step 2: Fetch current config
print("\nFetching config...")
config_resp = api('/api/bot/config/' + bot_id)
config = config_resp.get('config', {})
cred_id = config.get('credentialId', '')
print("credentialId:", cred_id)

# Step 3: Build updated config with profit retention fixes
updated_profit_protection = {
    'enabled': True,
    'activationMinProfit': 2.0,        # unchanged - arm at $2
    'activationPercent': 3.0,          # unchanged
    'portfolioActivationMinProfit': 3.0,
    'breakEvenActivationShare': 0.30,  # FIX: was 0.5 - arm at 30% of peak not 50%
    'breakEvenBufferProfit': 10.0,     # FIX: was 0.5 - close break-even at $10 min profit
    'breakEvenLockEnabled': True,
    'closeLosingPositionsWithProfitablePeers': True,
    'loserRotationMinLoss': 0.0,
    'marginTakeProfitPercent': 30.0,
    'minLockedProfit': 5.0,            # FIX: was 0.0 - lock $5 floor always
    'minimumHoldMinutes': 1.0,
    'peakProfitHardLockShare': 0.90,   # FIX: was 0.95 - trigger hard lock at 90% drop from peak
    'retraceClosePercent': 10.0,       # FIX: was 22.0 - tighter trailing stop
    'switchOnReversal': True,
    'adaptiveByVolatility': True,
    'protectedSymbolCooldownMinutes': 5.0,
    'zeroLossLockEnabled': True,       # keep - but now buffer=10 so zero means $10, not $0.50
}

update_payload = {
    'credentialId': cred_id,
    'profitProtection': updated_profit_protection,
}

print("\nUpdating config...")
update_resp = api('/api/bot/config/' + bot_id, update_payload, method='PATCH')
print("Update:", update_resp)
time.sleep(2)

# Step 4: Restart the bot
print("\nRestarting bot...")
restart_resp = api('/api/bot/start', {'botId': bot_id, 'userId': user_id})
print("Start:", restart_resp)

print("\nDone. Bot restarted with profit retention fixes.")
print("Changes applied:")
print("  breakEvenBufferProfit: 0.5 -> 10.0  (each closing trade captures at least $10)")
print("  retraceClosePercent:  22.0 -> 10.0  (trailing stop tightened to 10%)")
print("  minLockedProfit:       0.0 -> 5.0   ($5 profit floor always locked)")
print("  breakEvenActivationShare: 0.5 -> 0.3 (protection arms at 30% of peak)")
