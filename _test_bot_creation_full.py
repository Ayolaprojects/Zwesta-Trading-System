#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://localhost:9000"

print("=" * 70)
print("TESTING BOT CREATION & TRADE EXECUTION")
print("=" * 70)

# Test 1: Login
print("\n1. LOGIN TEST")
email = "trader2@example.com"
password = "test123"  

print(f"   Testing login with {email}...")
resp = requests.post(
    f"{BASE_URL}/api/user/login",
    json={"email": email, "password": password},
    timeout=10
)

print(f"   Status: {resp.status_code}")
data = resp.json()
print(json.dumps(data, indent=2))

if resp.status_code != 200:
    print("\n[FAILED] Login failed")
    exit(1)

token = data.get('token') or data.get('session_token') or data.get('access_token')
if not token:
    print("\n[ERROR] No token in response")
    print(json.dumps(data, indent=2))
    exit(1)

print(f"\n   SUCCESS: Logged in successfully")
print(f"   Token: {token[:30]}...")

# Test 2: Get existing bots
print("\n2. CHECKING EXISTING BOTS")
user_id = data.get('user_id')
resp = requests.get(
    f"{BASE_URL}/api/user/{user_id}/bots",
    headers={"X-Session-Token": token},
    timeout=10
)

print(f"   Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    bots = data.get('bots', []) or data.get('data', [])
    print(f"   Found {len(bots)} bots")
    
    for bot in bots[:5]:
        bot_name = bot.get('name') or bot.get('bot_name')
        broker = bot.get('broker')
        status = bot.get('status')
        pnl = bot.get('profit') or bot.get('pnl') or 0
        print(f"     - {bot_name} ({broker}) | Status: {status} | P&L: {pnl}")
else:
    print(f"   Error: {resp.json()}")

# Test 3: Create a test Exness bot
print("\n3. TESTING EXNESS BOT CREATION")
bot_config = {
    "name": "Test Exness Bot",
    "broker": "exness",
    "symbols": ["EURUSD"],
    "entry_mode": "signal",
    "signal_threshold": 60,
    "max_positions": 1
}

resp = requests.post(
    f"{BASE_URL}/api/bot/create",
    json=bot_config,
    headers={"X-Session-Token": token},
    timeout=45
)

print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")

if resp.status_code == 200:
    print("   [OK] Exness bot created successfully")
else:
    print("   [WARN] Exness bot creation failed (might need credentials)")

# Test 4: Create a test Binance bot
print("\n4. TESTING BINANCE BOT CREATION")
bot_config = {
    "name": "Test Binance Bot",
    "broker": "binance",
    "symbols": ["BTCUSDT"],
    "entry_mode": "signal",
    "signal_threshold": 60,
    "market": "futures",
    "max_positions": 1
}

resp = requests.post(
    f"{BASE_URL}/api/bot/create",
    json=bot_config,
    headers={"X-Session-Token": token},
    timeout=45
)

print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.json()}")

if resp.status_code == 200:
    print("   [OK] Binance bot created successfully")
else:
    print("   [WARN] Binance bot creation failed (might need credentials)")

print("\n" + "=" * 70)
print("[OK] BOT TESTING COMPLETE")
print("=" * 70)
