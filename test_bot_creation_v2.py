#!/usr/bin/env python3
"""
Test bot creation and persistence - CORRECT API FORMAT
"""
import os
import sys
import json
import time
import requests

# Config
BACKEND_URL = "http://localhost:9000"
TEST_EMAIL = "zwexman@gmail.com"
TEST_PASSWORD = "testpass"

def login():
    """Login and get session token"""
    resp = requests.post(
        f"{BACKEND_URL}/api/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        token = data.get('session_token')
        user_id = data.get('user_id')
        print(f"✅ Login successful")
        print(f"   Token: {token[:30]}...")
        print(f"   User: {user_id}")
        return token, user_id
    else:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return None, None

def get_credentials(token, user_id):
    """Get available credentials for user"""
    headers = {"X-Session-Token": token}
    resp = requests.get(
        f"{BACKEND_URL}/api/broker/credentials",
        headers=headers,
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and 'credentials' in data:
            creds = data['credentials']
        else:
            creds = data if isinstance(data, list) else []
        
        if creds:
            print(f"\n✅ Found {len(creds)} credential(s)")
            for cred in creds[:1]:  # Show first one
                cred_id = cred.get('credential_id') or cred.get('id')
                broker = cred.get('broker_name') or cred.get('broker')
                print(f"   ID: {cred_id}")
                print(f"   Broker: {broker}")
                return cred_id
        else:
            print(f"⚠️  No credentials found")
            return None
    else:
        print(f"❌ Get credentials failed: {resp.status_code}")
        return None

def create_bot(token, credential_id):
    """Create bot via correct API"""
    headers = {"X-Session-Token": token}
    
    payload = {
        "credentialId": credential_id,
        "botId": f"test-bot-{int(time.time())}",
        "symbols": ["EURUSD", "GBPUSD"],
        "strategy": "Trend Following",
        "riskPerTrade": 20,
        "maxDailyLoss": 60
    }
    
    print(f"\n📤 POST /api/bot/create")
    print(f"   Credential: {credential_id}")
    print(f"   Symbols: {payload['symbols']}")
    
    resp = requests.post(
        f"{BACKEND_URL}/api/bot/create",
        json=payload,
        headers=headers,
        timeout=15
    )
    
    print(f"\n📥 Response: {resp.status_code}")
    data = resp.json()
    
    if resp.status_code in [200, 201]:
        bot_id = data.get('botId') or data.get('bot_id')
        print(f"✅ Bot created successfully")
        print(f"   Bot ID: {bot_id}")
        return bot_id
    else:
        print(f"❌ Bot creation failed")
        print(f"   Error: {data.get('error') or data.get('message')}")
        print(f"   Full response: {json.dumps(data, indent=2)}")
        return None

def verify_bot_in_db(bot_id):
    """Verify bot was persisted to Postgres"""
    if not bot_id:
        return False
    
    time.sleep(1)  # Give DB time to sync
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        load_dotenv('C:/backend/.env')
        
        db_url = os.getenv('DATABASE_URL', 'postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading')
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute("SELECT bot_id, user_id, created_at FROM user_bots WHERE bot_id = %s", (bot_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            print(f"\n✅ Bot found in Postgres")
            print(f"   Bot ID: {row[0]}")
            print(f"   User: {row[1]}")
            print(f"   Created: {row[2]}")
            return True
        else:
            print(f"\n❌ Bot NOT found in Postgres")
            return False
    except Exception as e:
        print(f"\n⚠️  Could not verify in Postgres: {e}")
        return False

def main():
    print("=" * 70)
    print("BOT CREATION TEST - CORRECT API FORMAT")
    print("=" * 70)
    
    # Step 1: Login
    print("\n[STEP 1] Logging in...")
    token, user_id = login()
    if not token:
        return False
    
    # Step 2: Get credentials
    print("\n[STEP 2] Getting available credentials...")
    credential_id = get_credentials(token, user_id)
    if not credential_id:
        print("⚠️  Skipping bot creation - no credentials available")
        return False
    
    # Step 3: Create bot
    print("\n[STEP 3] Creating test bot...")
    bot_id = create_bot(token, credential_id)
    if not bot_id:
        return False
    
    # Step 4: Verify persistence
    print("\n[STEP 4] Verifying persistence to Postgres...")
    success = verify_bot_in_db(bot_id)
    
    if success:
        print("\n" + "=" * 70)
        print("✅ BOT CREATION & PERSISTENCE TEST PASSED")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ BOT CREATION TEST FAILED")
        print("=" * 70)
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
