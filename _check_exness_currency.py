import sqlite3, json, requests

BASE = 'http://148.113.5.39:9000'
EXNESS_CRED = '9f14c8b4-0071-4222-81a2-5c99e841b9e0'
EXNESS_BOT  = 'bot_1779057251465'

# ── 1. Check VPS DB via API for account currency ──────────────────────────────
r = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=15)
tok = r.json()['session_token']
h = {'X-Session-Token': tok}

# Get dashboard accounts to see what currency is coming back from the VPS
accts = requests.get(f'{BASE}/api/dashboard/accounts', headers=h, timeout=20).json()
print("=== ACCOUNTS ===")
for broker, entries in accts.get('brokers', {}).items():
    for e in entries:
        print(f"  {broker} acct={e.get('accountNumber')} cred={e.get('credentialId','?')[:20]} currency={e.get('currency')} displayCurrency={e.get('displayCurrency')} balance={e.get('balance')}")

# ── 2. Check/show current bot config ──────────────────────────────────────────
cfg_resp = requests.get(f'{BASE}/api/bot/config/{EXNESS_BOT}', headers=h, timeout=15).json()
cfg = cfg_resp.get('config', {})
print("\n=== EXNESS BOT CONFIG ===")
for k in ['brokerName','credentialId','displayCurrency','accountCurrency','tradeAmount','fixedTradeAmount','symbols','riskPerTrade']:
    print(f"  {k}: {cfg.get(k)}")
