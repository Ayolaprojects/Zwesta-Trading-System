"""
Fix VPS bot_1778193263218 by stopping it, waiting for thread to die, then updating tradeAmount.
"""
import requests, json, time

VPS = 'http://148.113.5.39:9000'
TOKEN = 'd2e93e00da2e04cdd815475b17a61cc6cbcdf02a75cc2a5ef9c3e9c472da3cc5'
H = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
BOT = 'bot_1778193263218'

def api(method, path, data=None):
    fn = getattr(requests, method)
    r = fn(f'{VPS}{path}', headers=H, json=data, timeout=25)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, r.text

print("Step 1: Stop the bot")
code, resp = api('post', f'/api/bot/stop/{BOT}')
print(f"  {code}: {resp}")

if code != 200:
    print("Stop failed! Trying to proceed anyway...")

print("\nStep 2: Wait 40s for thread to die...")
for i in range(40, 0, -5):
    print(f"  {i}s remaining...")
    time.sleep(5)

print("\nStep 3: Try updating config")
code, resp = api('put', f'/api/bot/config/{BOT}', {
    'tradeAmount': 500,
    'riskPerTrade': 2.0,
    'dynamicSizing': True,
    'credentialId': '641ce2a4-19a7-44f3-a4a7-6e8df5a9c4e9',
})
print(f"  {code}: {resp}")

if code == 409:
    print("\n  Thread still alive. Trying once more after 30s...")
    time.sleep(30)
    code, resp = api('put', f'/api/bot/config/{BOT}', {
        'tradeAmount': 500,
        'riskPerTrade': 2.0,
        'dynamicSizing': True,
        'credentialId': '641ce2a4-19a7-44f3-a4a7-6e8df5a9c4e9',
    })
    print(f"  {code}: {resp}")

if code == 200:
    print("\nStep 4: Restart bot")
    time.sleep(2)
    code, resp = api('post', '/api/bot/start', {'botId': BOT})
    print(f"  {code}: {resp}")

    print("\nStep 5: Verify new config")
    time.sleep(3)
    code, resp = api('get', f'/api/bot/config/{BOT}')
    cfg = resp.get('config', resp) if isinstance(resp, dict) else {}
    print(f"  effectiveTradeAmount: {cfg.get('effectiveTradeAmount')}")
    print(f"  tradeAmount: {cfg.get('tradeAmount')}")
else:
    print(f"\nConfig update still failing ({code}). Need RDP access to VPS to fix this directly.")
    print("Alternatively: restart the VPS backend process to reset all bot threads.")
