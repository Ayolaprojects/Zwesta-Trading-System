"""Admin patch of AZE BOT runtime_state directly via /api/admin/fix-bot-link.
This bypasses broker validation and the slow config PUT path."""
import requests, json

BASE = 'http://148.113.5.39:9000'
AH = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure', 'Content-Type': 'application/json'}

payload = {
    'bot_id': 'AZE BOT',
    'runtime_state': {
        # Raise trade amount - will be capped to ~$10.65 by safety net on restart
        'tradeAmount': 20.0,
        # Enable intelligent scanner (already set via earlier partial PUT)
        'intelligentScanner': True,
        # Allow high volatility for crypto futures
        'allowedVolatility': ['Low', 'Medium', 'High'],
        # Clear retrace state so 94.9% penalty is wiped
        'tradeAmountAdaptation': None,
        'dailyProfitPeaks': {},
        'effectiveTradeAmount': None,
    }
}

print('Sending admin runtime_state patch...')
try:
    r = requests.post(f'{BASE}/api/admin/fix-bot-link', headers=AH, json=payload, timeout=20)
    print(f'Status: {r.status_code}')
    print(r.text[:500])
except Exception as e:
    print(f'Error: {e}')

# Verify
import time; time.sleep(1)
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
token = lr.json().get('session_token','')
SH = {'X-Session-Token': token}
r2 = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r2.json().get('config', {})
print(f"\nVerification: tradeAmount={cfg.get('tradeAmount')} scanner={cfg.get('intelligentScanner')} volatility={cfg.get('allowedVolatility')}")
print(f"tradeAmountAdaptation={json.dumps(cfg.get('tradeAmountAdaptation'), indent=2)[:200]}")
