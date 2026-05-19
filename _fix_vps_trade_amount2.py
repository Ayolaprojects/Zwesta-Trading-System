"""
Aggressive fix: stop-all, then restart only the bot we want with proper config.
"""
import requests, json, time

VPS = 'http://148.113.5.39:9000'
TOKEN = 'd2e93e00da2e04cdd815475b17a61cc6cbcdf02a75cc2a5ef9c3e9c472da3cc5'
H = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
BOT = 'bot_1778193263218'
CRED = '641ce2a4-19a7-44f3-a4a7-6e8df5a9c4e9'

def api(method, path, data=None):
    fn = getattr(requests, method)
    r = fn(f'{VPS}{path}', headers=H, json=data, timeout=25)
    try:
        return r.status_code, r.json()
    except:
        return r.status_code, r.text

print("=== Stop bot (again) ===")
code, resp = api('post', f'/api/bot/stop/{BOT}')
print(code, resp)

print("\nWaiting 130s (one full cycle + buffer) for thread to exit...")
for i in range(130, 0, -10):
    print(f"  {i}s ...")
    time.sleep(10)

print("\n=== Try config update ===")
code, resp = api('put', f'/api/bot/config/{BOT}', {
    'tradeAmount': 500,
    'riskPerTrade': 2.0,
    'dynamicSizing': True,
    'credentialId': CRED,
})
print(code, resp)

if code == 200:
    print("\nSuccess! Restarting bot...")
    time.sleep(2)
    code2, resp2 = api('post', '/api/bot/start', {'botId': BOT})
    print(code2, resp2)
    time.sleep(5)
    code3, resp3 = api('get', f'/api/bot/config/{BOT}')
    cfg = resp3.get('config', {}) if isinstance(resp3, dict) else {}
    print("effectiveTradeAmount:", cfg.get('effectiveTradeAmount'))
    print("tradeAmount:", cfg.get('tradeAmount'))
else:
    print("\nConfig update failed. Backend needs a full restart to clear stuck threads.")
    print("Options:")
    print("1. RDP into 148.113.5.39, open PowerShell and run:")
    print("   Get-Process python | Stop-Process -Force")
    print("   cd C:\\backend")
    print("   python multi_broker_backend_updated.py")
    print()
    print("2. OR ask your VPS provider for a restart option in their control panel")
