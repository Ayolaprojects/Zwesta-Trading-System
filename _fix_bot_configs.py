"""
Fix bot configuration issues:

Exness (bot_1778274193141):
  - Paused: daily loss R165.84 hit R160 limit on just 2 trades
  - Fix: raise maxDailyLoss to R500, lower riskPerTrade to 3, switch to 'balanced' profile
  - Stop → reconfigure → restart (new limit R500 > current loss R165, so bot won't re-pause)

Binance (bot_1778274751313):
  - signalThreshold=1 → too permissive, 33% win rate on closed trades
  - Fix: raise to 55 for better signal quality
  - Bot currently holds 3 open profitable positions — DON'T stop it
"""
import requests, time, json

VPS = 'http://148.113.5.39:9000'

# Re-auth
r = requests.post(f'{VPS}/api/user/login',
                  json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=10)
r.raise_for_status()
TOKEN = r.json()['session_token']
H = {'X-Session-Token': TOKEN, 'Content-Type': 'application/json'}
print(f"Logged in. Token: {TOKEN[:20]}...")

EXNESS_BOT = 'bot_1778274193141'
BINANCE_BOT = 'bot_1778274751313'

# ─────────────────────────────────────────────
# 1. EXNESS — stop the bot (it's paused/blocked)
# ─────────────────────────────────────────────
print("\n[1] Stopping Exness bot...")
r = requests.post(f'{VPS}/api/bot/stop/{EXNESS_BOT}', headers=H, timeout=15)
print(f"  Stop response: {r.status_code} — {r.text[:120]}")

print("  Waiting 135s for bot thread to die...")
for i in range(135, 0, -10):
    time.sleep(10)
    print(f"    {i}s remaining...")

# ─────────────────────────────────────────────
# 2. EXNESS — update config
#    - maxDailyLoss: 160 → 500  (room for ~6 normal losing trades)
#    - riskPerTrade: 30 → 3     (conservative risk per trade)
#    - managementProfile: fast_growth → balanced
#    - tradeAmount: 869.73 → 600  (slightly smaller)
#    - Keep signalThreshold: 72  (already selective)
# ─────────────────────────────────────────────
print("\n[2] Updating Exness bot config...")
new_exness_cfg = {
    'credentialId': '8a2a185c-eb95-4803-8590-9523ae0a9c4d',
    'maxDailyLoss': 500.0,
    'riskPerTrade': 3.0,
    'tradeAmount': 600.0,
    'managementProfile': 'balanced',
    'signalThreshold': 72,
    'maxOpenPositions': 3,
}
r = requests.put(f'{VPS}/api/bot/config/{EXNESS_BOT}', headers=H, json=new_exness_cfg, timeout=15)
print(f"  Config update: {r.status_code} — {r.text[:200]}")
if r.status_code == 409:
    print("  !! Thread still alive — waiting another 130s...")
    for i in range(130, 0, -10):
        time.sleep(10)
        print(f"    {i}s remaining...")
    r = requests.put(f'{VPS}/api/bot/config/{EXNESS_BOT}', headers=H, json=new_exness_cfg, timeout=15)
    print(f"  Config update retry: {r.status_code} — {r.text[:200]}")

if r.status_code not in (200, 201):
    print(f"  !! Config update failed. Aborting restart.")
else:
    print("  Config updated successfully.")

    # ─────────────────────────────────────────────
    # 3. EXNESS — restart
    #    New maxDailyLoss=500 > today's loss of 165, so bot will trade again
    # ─────────────────────────────────────────────
    print("\n[3] Starting Exness bot...")
    r = requests.post(f'{VPS}/api/bot/start', headers=H,
                      json={'botId': EXNESS_BOT}, timeout=15)
    print(f"  Start response: {r.status_code} — {r.text[:200]}")

# ─────────────────────────────────────────────
# 4. BINANCE — update signalThreshold only
#    Bot has 3 open positions — we only update config on running bot via PUT
#    (the PUT endpoint won't allow changes on a running bot, so we just
#     note the current state and will update after positions close)
# ─────────────────────────────────────────────
print("\n[4] Checking Binance bot open positions before any config change...")
r = requests.get(f'{VPS}/api/bot/status', headers=H, timeout=15)
bots = r.json().get('bots', [])
binance = next((b for b in bots if b['botId'] == BINANCE_BOT), None)
if binance:
    open_pos = binance.get('openPositions', [])
    print(f"  Open positions: {len(open_pos)}")
    for p in open_pos:
        print(f"    {p['symbol']} {p['type']} @ {p['entryPrice']} → profit={p['profit']} | SL={p['stopLossPrice']:.2f} | TP={p['takeProfitPrice']:.2f}")
    
    if len(open_pos) == 0:
        print("  No open positions — safe to reconfigure Binance bot.")
        print("\n  Stopping Binance bot to update signal threshold...")
        r = requests.post(f'{VPS}/api/bot/stop/{BINANCE_BOT}', headers=H, timeout=15)
        print(f"  Stop: {r.status_code} — {r.text[:120]}")
        
        print("  Waiting 135s...")
        for i in range(135, 0, -10):
            time.sleep(10)
            print(f"    {i}s remaining...")
        
        new_binance_cfg = {
            'credentialId': 'bf86a3a3-91e2-4bf4-93a7-13ac3539cbd8',
            'signalThreshold': 55,   # was 1 — raise to filter weak signals
            'maxDailyLoss': 160.0,   # keep same
            'riskPerTrade': 3.0,     # lower from 30
            'tradeAmount': 252.77,   # keep same base
            'managementProfile': 'balanced',
        }
        r = requests.put(f'{VPS}/api/bot/config/{BINANCE_BOT}', headers=H, json=new_binance_cfg, timeout=15)
        print(f"  Config update: {r.status_code} — {r.text[:200]}")
        
        r = requests.post(f'{VPS}/api/bot/start', headers=H,
                          json={'botId': BINANCE_BOT}, timeout=15)
        print(f"  Start: {r.status_code} — {r.text[:200]}")
    else:
        print(f"\n  Binance has {len(open_pos)} open positions — NOT stopping.")
        print("  signalThreshold will be updated AFTER positions close.")
        print("  Action: re-run this section manually when positions are closed.")

# ─────────────────────────────────────────────
# 5. Verify final state
# ─────────────────────────────────────────────
print("\n[5] Final bot status check...")
r = requests.get(f'{VPS}/api/bot/status', headers=H, timeout=15)
bots = r.json().get('bots', [])
for b in bots:
    print(f"\n  Bot: {b['botId']}")
    print(f"    Broker: {b.get('broker_type')} | Status: {b.get('status')}")
    print(f"    Pause: {b.get('pauseReason')}")
    print(f"    Trades: {b.get('totalTrades')} | P/L: {b.get('totalProfit')} | WinRate: {b.get('winRate')}%")
    print(f"    EffTradeAmt: {b.get('effectiveTradeAmount')}")
    open_p = b.get('openPositions', [])
    print(f"    Open positions: {len(open_p)}")
