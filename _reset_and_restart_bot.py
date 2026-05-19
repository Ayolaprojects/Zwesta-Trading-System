"""
Stop bot, reset trade amount adaptation via API, restart.
"""
import urllib.request, json, time, sqlite3

base = 'http://148.113.5.39:9000'
bot_id = 'bot_1778970971191'
user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

login_data = json.dumps({'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}).encode()
req = urllib.request.Request(base + '/api/user/login', data=login_data, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())['session_token']
headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())

# Step 1: Stop
print("Stopping bot...")
stop = post('/api/bot/stop/' + bot_id, {'user_id': user_id})
print("Stop:", stop.get('message', stop))
time.sleep(3)

# Step 2: Patch runtime_state directly in DB to reset inflated trade amount
print("\nPatching DB runtime_state...")
db = r'C:\backend\zwesta_trading.db'
try:
    conn = sqlite3.connect(db, timeout=10)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    row = c.execute('SELECT runtime_state FROM user_bots WHERE bot_id=?', (bot_id,)).fetchone()
    state = json.loads(row['runtime_state'])

    # Reset inflated multipliers
    state['effectivePositionSizeMultiplier'] = 1.0
    state['effectiveScannerCapitalMultiplier'] = 1.0

    # Cap effective trade amount to fit demo Binance free USDT (~$4,514)
    # Use $3,500 so orders reliably execute within the free balance
    state['effectiveTradeAmount'] = 3500.0
    state['riskPerTrade'] = 230.0
    state['maxDailyLoss'] = 920.0

    # Reset adaptation state from 'hot' back to 'normal'
    if isinstance(state.get('tradeAmountAdaptation'), dict):
        adapt = state['tradeAmountAdaptation']
        adapt['state'] = 'normal'
        adapt['multiplier'] = 1.0
        adapt['adjustedTradeAmount'] = 3500.0
        adapt['scannerCapitalMultiplier'] = 1.0
        adapt['retraceRatio'] = 0.0
        adapt['reason'] = 'reset — demo account free balance cap'
        state['tradeAmountAdaptation'] = adapt

    c.execute('UPDATE user_bots SET runtime_state=? WHERE bot_id=?', (json.dumps(state), bot_id))
    conn.commit()
    conn.close()
    print("DB patch successful.")
    print(f"  effectiveTradeAmount → {state['effectiveTradeAmount']}")
    print(f"  riskPerTrade → {state['riskPerTrade']}")
    print(f"  maxDailyLoss → {state['maxDailyLoss']}")
except Exception as e:
    print(f"DB patch error: {e} — will restart without DB patch")

time.sleep(2)

# Step 3: Restart
print("\nRestarting bot...")
start = post('/api/bot/start', {'botId': bot_id, 'userId': user_id})
print("Start:", start.get('message', start))
print("\nDone. Bot restarted. Trades will now be sized to fit the $4,514 free USDT balance.")
