"""
Fix Exness bot ZAR account currency:
1. Re-save the Exness credential => triggers MT5 connect on VPS => sets account_currency=ZAR
2. Stop the bot
3. PATCH bot config with proper ZAR trade amount
4. Restart the bot
"""
import requests, json, time

BASE = 'http://148.113.5.39:9000'
EXNESS_CRED = '9f14c8b4-0071-4222-81a2-5c99e841b9e0'
EXNESS_BOT  = 'bot_1779057251465'
USER_ID     = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
ADMIN_HDR   = {'Authorization': 'Bearer zwesta_live_api_key_2026_secure', 'Content-Type': 'application/json'}

r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
tok = r.json()['session_token']
h = {'X-Session-Token': tok, 'Content-Type': 'application/json'}
print("Logged in OK")

# ── Step 1: Re-save credential to trigger MT5 currency capture on VPS ─────────
print("\n[1] Re-saving Exness credential to force ZAR account_currency capture...")
cred_payload = {
    "brokerName": "Exness",
    "accountNumber": "295677214",
    "password": "Ithemba@2026",
    "server": "Exness-MT5Real27",
    "isLive": True,
    "label": "Exness ZAR Live",
}
resp = requests.post(f'{BASE}/api/broker/credentials', headers=h, json=cred_payload, timeout=60)
print(f"  Status: {resp.status_code}")
try:
    rj = resp.json()
    print(f"  Response: {json.dumps(rj, indent=2)[:500]}")
except:
    print(f"  Raw: {resp.text[:300]}")

# ── Step 2: Stop the bot ──────────────────────────────────────────────────────
print("\n[2] Stopping Exness bot...")
stop_resp = requests.post(f'{BASE}/api/bot/stop', headers=h, json={'botId': EXNESS_BOT, 'user_id': USER_ID}, timeout=20)
print(f"  Stop: {stop_resp.status_code} {stop_resp.text[:100]}")
time.sleep(3)

# ── Step 3: PATCH bot config with proper ZAR trade amount ────────────────────
# R1,350 balance. R500/trade = ~37%. Sensible for live trading start.
print("\n[3] Patching bot config with ZAR trade amount R500...")
BALANCE_ZAR = 1350.0
TRADE_ZAR   = 500.0   # R500 per trade — adjust as needed

patch_payload = {
    "tradeAmount":      TRADE_ZAR,
    "displayCurrency":  "ZAR",
    # fixedTradeAmount keeps lot size stable rather than % of equity
}
patch_resp = requests.patch(f'{BASE}/api/bot/config/{EXNESS_BOT}', headers=h, json=patch_payload, timeout=30)
print(f"  PATCH: {patch_resp.status_code}")
try:
    print(f"  {json.dumps(patch_resp.json(), indent=2)[:400]}")
except:
    print(f"  {patch_resp.text[:200]}")

# ── Step 4: Verify new config ─────────────────────────────────────────────────
print("\n[4] Verifying updated bot config...")
cfg_resp = requests.get(f'{BASE}/api/bot/config/{EXNESS_BOT}', headers=h, timeout=15).json()
cfg = cfg_resp.get('config', {})
for k in ['brokerName','displayCurrency','accountCurrency','tradeAmount','fixedTradeAmount','symbols']:
    print(f"  {k}: {cfg.get(k)}")

# ── Step 5: Verify credential currency updated ────────────────────────────────
print("\n[5] Checking credential account_currency after re-save...")
cred_det = requests.get(f'{BASE}/api/accounts/{EXNESS_CRED}/details', headers=h, timeout=20).json()
acct = cred_det.get('account', {})
lai  = acct.get('liveAccountInfo', {})
print(f"  liveAccountInfo.currency: {lai.get('currency')}")
print(f"  balance: {acct.get('balance')}")

# ── Step 6: Restart bot ───────────────────────────────────────────────────────
print("\n[6] Restarting Exness bot...")
start_resp = requests.post(f'{BASE}/api/bot/start', headers=h,
    json={'botId': EXNESS_BOT, 'user_id': USER_ID}, timeout=20)
print(f"  Start: {start_resp.status_code} {start_resp.text[:150]}")
