import requests, json, time

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
uid   = d.get('user_id','')
SH = {'X-Session-Token': token}
BOT_ID = 'AZE BOT'

# 1. Stop bot
print('--- Step 1: Stopping bot ---')
r = requests.post(f'{BASE}/api/bot/stop/{requests.utils.quote(BOT_ID)}', headers=SH, timeout=15)
print(f'Stop: {r.status_code} {r.text[:200]}')
time.sleep(3)

# 2. Fetch current config to preserve all fields
print('\n--- Step 2: Fetching current config ---')
r = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r.json().get('config', {})
print(f"credentialId: {cfg.get('credentialId')}")
print(f"Current tradeAmount: {cfg.get('tradeAmount')}")
print(f"Current effectiveTradeAmount: {cfg.get('effectiveTradeAmount')}")
print(f"Current intelligentScanner: {cfg.get('intelligentScanner')}")
print(f"Current allowedVolatility: {cfg.get('allowedVolatility')}")

# 3. Patch config — send full update including required fields
print('\n--- Step 3: Patching config ---')
patch = {
    'credentialId': cfg.get('credentialId'),
    # Fix 1: Raise trade amount to ~22% of $88.75 balance = ~$20
    'tradeAmount': 20.0,
    # Fix 2: Enable intelligent scanner for better signal quality
    'intelligentScanner': True,
    # Fix 3: Include High volatility — crypto futures need it
    'allowedVolatility': ['Low', 'Medium', 'High'],
    # Fix 4: Clear retrace state so 94.9% retrace penalty is wiped
    'tradeAmountAdaptation': None,
    'dailyProfitPeaks': {},
    'effectiveTradeAmount': None,
    # Keep everything else as-is
    'symbols': cfg.get('symbols'),
    'strategy': cfg.get('strategy'),
    'signalThreshold': cfg.get('signalThreshold'),
    'managementProfile': cfg.get('managementProfile'),
    'maxDailyLoss': cfg.get('maxDailyLoss'),
    'maxOpenPositions': cfg.get('maxOpenPositions'),
    'riskPerTrade': cfg.get('riskPerTrade'),
}
r2 = requests.put(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, json=patch, timeout=15)
print(f'Patch: {r2.status_code} {r2.text[:400]}')

if r2.status_code not in (200, 201):
    print('Patch failed — aborting')
    exit(1)

time.sleep(2)

# 4. Restart bot
print('\n--- Step 4: Restarting bot ---')
# Get activation pin
pin_r = requests.post(f'{BASE}/api/bot/AZE%20BOT/request-activation', headers=SH, timeout=10)
print(f'Request activation: {pin_r.status_code} {pin_r.text[:200]}')
pin_data = pin_r.json() if pin_r.ok else {}
pin = pin_data.get('activation_pin','')

if pin:
    start_r = requests.post(f'{BASE}/api/bot/start', headers=SH,
                             json={'bot_id': BOT_ID, 'activation_pin': pin}, timeout=15)
    print(f'Start: {start_r.status_code} {start_r.text[:300]}')
else:
    print('No activation pin returned — bot may need manual restart from app')

# 5. Verify
time.sleep(4)
print('\n--- Step 5: Verifying updated config ---')
r3 = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg2 = r3.json().get('config', {})
print(f"tradeAmount: {cfg2.get('tradeAmount')}")
print(f"effectiveTradeAmount: {cfg2.get('effectiveTradeAmount')}")
print(f"intelligentScanner: {cfg2.get('intelligentScanner')}")
print(f"allowedVolatility: {cfg2.get('allowedVolatility')}")
print(f"PSM: {cfg2.get('effectivePositionSizeMultiplier')}")
print(f"tradeAmountAdaptation: {json.dumps(cfg2.get('tradeAmountAdaptation'), indent=2)}")
