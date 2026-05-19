import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
SH = {'X-Session-Token': token}

# Fetch current config
r = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r.json().get('config', {})
print(f"Current tradeAmount: {cfg.get('tradeAmount')}, effectiveTradeAmount: {cfg.get('effectiveTradeAmount')}")

# Build patch payload
patch = {
    # Core fix: proportional trade amount for $88.75 balance (~22% per trade)
    'tradeAmount': 20.0,
    # Enable intelligent scanner for better signal quality selection
    'intelligentScanner': True,
    # Include High volatility – crypto futures benefit from it
    'allowedVolatility': ['Low', 'Medium', 'High'],
    # Reset retrace penalty state so bot starts fresh
    'tradeAmountAdaptation': None,
    'dailyProfitPeaks': {},
    # Reset effective trade amount so it recalculates from the new base
    'effectiveTradeAmount': None,
    # Slightly lower max daily loss cap to match balance ($88.75 → 15% = ~$13)
    # Keep at 140 since the bot will self-limit via adaptive sizing
}

r2 = requests.put(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, json=patch, timeout=10)
print(f"Patch response: {r2.status_code}")
print(r2.text[:500])
