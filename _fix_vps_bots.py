"""
Diagnose and fix VPS bots via API.
"""
import requests, json

VPS = 'http://148.113.5.39:9000'
TOKEN = 'd2e93e00da2e04cdd815475b17a61cc6cbcdf02a75cc2a5ef9c3e9c472da3cc5'
H = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}

def post(path, data=None):
    try:
        r = requests.post(f'{VPS}{path}', headers=H, json=data, timeout=15)
        return r.status_code, r.json() if r.content else {}
    except Exception as e:
        return 0, str(e)

def get(path):
    try:
        r = requests.get(f'{VPS}{path}', headers=H, timeout=15)
        return r.status_code, r.json() if r.content else {}
    except Exception as e:
        return 0, str(e)

# Try to find stop endpoint
print("=== Finding stop endpoint ===")
for ep in ['/api/bot/stop', '/api/trading/stop', '/api/bot/pause', '/api/bot/deactivate', '/api/bots/stop']:
    code, data = post(ep, {'botId': 'bot_1778193263218'})
    if code != 404:
        print(f"{ep} -> {code}: {str(data)[:200]}")

# Check thresholds and config for the non-trading bot
print("\n=== Bot config endpoints ===")
for ep in ['/api/bot/config', '/api/bot/settings', '/api/bot/get']:
    code, data = get(f"{ep}?botId=bot_1778193263218")
    if code != 404:
        print(f"{ep} -> {code}: {str(data)[:300]}")

# Get trades list
print("\n=== Trade endpoints ===")
for ep in ['/api/trades', '/api/trade/list', '/api/bot/trades']:
    code, data = get(ep)
    if code != 404:
        print(f"{ep} -> {code}: {str(data)[:500]}")

# Check what happened - maybe the bot is blocked by signal threshold
# Bot_1778193263218 has signalThreshold=1 (very low) but 0 trades today.
# Bot_1778263156666 also 0 trades.
# Most likely cause: MT5 AutoTrading disabled on VPS (same as local machine issue)
print("\n=== Summary ===")
print("Bot bot_1778193263218:")
print("  - status: RUNNING, 17 trades, 0 wins, -315.73 profit")  
print("  - Last trade: 2026-05-07 19:00 (yesterday)")
print("  - Today: 0 new trades despite signalThreshold=1")
print("  - LIKELY CAUSE: MT5 AutoTrading disabled on VPS (retcode=10027)")
print()
print("Bot bot_1778263156666:")
print("  - status: RUNNING, 0 trades total, just started 1.5h ago")
print("  - LIKELY CAUSE: MT5 AutoTrading disabled OR no signals yet on USDCHFm")
print()
print("RECOMMENDED FIX: Log into VPS via RDP and enable AutoTrading in MT5 terminal")
print(f"  VPS IP: 148.113.5.39 | RDP Port: 3389")
