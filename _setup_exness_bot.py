#!/usr/bin/env python3
"""
Complete Exness Bot Setup Guide
Step 1: Add your Exness credentials
Step 2: Create GBPUSDm bot with pyramiding
"""
import requests
import json

API_BASE = 'http://localhost:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'

print("=" * 80)
print("EXNESS BOT SETUP - STEP-BY-STEP GUIDE")
print("=" * 80)
print()

# Login
print("[Step 1] Logging in...")
response = requests.post(
    f'{API_BASE}/api/user/login',
    json={'email': EMAIL, 'password': PASSWORD},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json().get('session_token')
print(f"✅ Logged in successfully\n")

# Instructions for adding credentials
print("=" * 80)
print("[Step 2] ADD EXNESS CREDENTIALS")
print("=" * 80)
print()
print("You need to add your Exness MT5 account credentials:")
print()
print("📱 Option 1: Use the Zwesta App (Recommended)")
print("   1. Open Zwesta app on your phone/PC")
print("   2. Go to: Accounts → Add Broker")
print("   3. Select: Exness")
print("   4. Enter your details:")
print("      • Account Number: (Your 9-digit MT5 account)")
print("      • Password: (Your MT5 password)")
print("      • Server: Exness-MT5Trial9 (demo) or Exness-Real (live)")
print("      • Account Type: Select LIVE or DEMO")
print("   5. Save")
print()
print("🖥️  Option 2: Use API (Advanced)")
print("   Run this command with your details:")
print()
print("   curl -X POST http://localhost:9000/api/broker/add-credential \\")
print("     -H 'X-Session-Token: YOUR_TOKEN' \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{")
print('         "broker_name": "Exness",')
print('         "account_number": "YOUR_ACCOUNT_NUMBER",')
print('         "password": "YOUR_PASSWORD",')
print('         "server": "Exness-MT5Trial9",')
print('         "is_live": false')
print("     }'")
print()
print("=" * 80)
print()
input("Press ENTER after you've added your Exness credentials in the app...")
print()

# Check if credentials were added
print("[Step 3] Checking for credentials...")
response = requests.get(
    f'{API_BASE}/api/broker/credentials',
    headers={'X-Session-Token': token},
    timeout=10
)

if response.status_code == 200:
    creds = response.json().get('credentials', [])
    exness_creds = [c for c in creds if 'Exness' in str(c.get('broker_name', ''))]
    
    if exness_creds:
        print(f"✅ Found {len(exness_creds)} Exness credential(s)")
        for cred in exness_creds:
            print(f"   • Account: {cred.get('account_number')} ({cred.get('server')})")
        
        # Use first credential
        credential_id = exness_creds[0].get('credential_id')
        
        print(f"\n[Step 4] Creating GBPUSDm bot with pyramiding...")
        
        bot_config = {
            'credentialId': credential_id,
            'name': 'GBP Pyramid Bot',
            'strategy': 'Trend Following',
            'symbols': ['GBPUSDm'],
            'managementProfile': 'balanced',  # ✅ Enables pyramiding
            'riskProfile': 'moderate',
            'tradeAmount': 128.38,  # 0.01 lot
            'fixedTradeVolume': 0.01,
            'maxOpenPositions': 3,
            'maxPositionsPerSymbol': 3,
            'maxDailyLoss': 50.0,
            'maxDrawdownPercent': 15.0,
            'signalThreshold': 60,
            'minRiskRewardRatio': 1.5,
            'profitProtection': {
                'enabled': True,
                'activationMinProfit': 5.0,
                'retraceClosePercent': 35.0,
                'breakEvenLockEnabled': True,
                'peakProfitHardLockShare': 0.9,
            },
        }
        
        response = requests.post(
            f'{API_BASE}/api/bot/create',
            json=bot_config,
            headers={'X-Session-Token': token, 'Content-Type': 'application/json'},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                bot_id = result.get('bot_id') or result.get('botId')
                print(f"\n✅ BOT CREATED SUCCESSFULLY!")
                print(f"\n{'=' * 80}")
                print(f"Bot ID: {bot_id}")
                print(f"Name: GBP Pyramid Bot")
                print(f"Symbol: GBPUSDm")
                print(f"\n📊 PYRAMIDING: ENABLED")
                print(f"   Profile: balanced")
                print(f"   Base: 0.01 lots (R128.38)")
                print(f"   Multipliers: 2x at R1-R4.99, 5x at R5+")
                print(f"\n🛡️  PROFIT PROTECTION: ENABLED")
                print(f"   Activation: R5.00")
                print(f"   Breakeven lock: ✅")
                print(f"   Peak lock: 90%")
                print(f"\n{'=' * 80}")
                print(f"\nBot is ready to trade!")
            else:
                print(f"❌ Failed: {result.get('error') or result}")
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:300]}")
    else:
        print(f"❌ No Exness credentials found yet.")
        print(f"\nPlease add them using the app, then run this script again.")
else:
    print(f"❌ Failed to check credentials: {response.text}")
