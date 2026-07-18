#!/usr/bin/env python3
"""
Test Binance Connection & Create Demo Trading Bot
This script tests your Binance API credentials and creates a bot with demo trading
"""

import requests
import json
import time
from datetime import datetime

import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:9000")
TARGET_USER_ID = os.getenv("TEST_USER_ID", "8e74db37-fd1e-4c57-87c4-ad3b64012ecf")


def _load_dotenv_if_available():
    try:
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
    except Exception:
        pass


def _get_latest_active_session_token(user_id: str):
    """Return a recent active session token for user_id from Postgres."""
    try:
        import psycopg2
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            return None

        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT token
            FROM user_sessions
            WHERE user_id = %s
                            AND is_active = TRUE
              AND (expires_at IS NULL OR expires_at > NOW()::text)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        print(f"⚠️ Could not load active session token from Postgres: {e}")
        return None


def _get_latest_binance_credentials(user_id: str):
    """Load the newest active Binance credentials for the user from Postgres."""
    try:
        import psycopg2
        from credential_crypto import decrypt_secret

        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            return None

        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT api_key, password, is_live, server
            FROM broker_credentials
            WHERE user_id = %s
              AND LOWER(broker_name) = 'binance'
                            AND is_active = TRUE
            ORDER BY COALESCE(updated_at, created_at, '') DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None

        api_key = decrypt_secret(row[0]) if row[0] else ''
        api_secret = decrypt_secret(row[1]) if row[1] else ''
        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'is_live': bool(row[2]),
            'market': str(row[3] or 'spot').strip().lower() or 'spot',
        }
    except Exception as e:
        print(f"⚠️ Could not load Binance credentials from Postgres: {e}")
        return None

# ==================== STEP 1: TEST BINANCE CONNECTION ====================
def test_binance_connection(session_token: str, api_key: str, api_secret: str, is_live: bool = False, market: str = "spot"):
    """Test Binance API connection and retrieve account info"""
    
    print("\n" + "="*70)
    print("🔌 STEP 1: Testing Binance Connection")
    print("="*70)
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-Token": session_token
    }
    
    payload = {
        "broker": "Binance",
        "api_key": api_key,
        "api_secret": api_secret,
        "is_live": is_live,
        "market": market  # "spot" or "futures"
    }
    
    print(f"\n📨 Sending connection test request...")
    print(f"   Broker: Binance")
    print(f"   Mode: {'LIVE' if is_live else 'DEMO/TESTNET'}")
    print(f"   Market: {market}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/broker/test-connection",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ CONNECTION SUCCESSFUL!\n")
            print(json.dumps(result, indent=2))
            
            credential_id = result.get('credential_id')
            balance = result.get('balance', 0)
            
            print(f"\n💾 Credential ID: {credential_id}")
            print(f"💰 Account Balance: ${balance:.2f}")
            
            return credential_id, balance
        else:
            print("\n❌ CONNECTION FAILED!\n")
            print(json.dumps(response.json(), indent=2))
            return None, None
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out - backend may not be running")
        return None, None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None, None


# ==================== STEP 2: CREATE DEMO TRADING BOT ====================
def create_demo_bot(session_token: str, credential_id: str, symbols: list = None, strategy: str = "Momentum Trading"):
    """Create a demo trading bot using the verified Binance credential"""
    
    if not credential_id:
        print("❌ Skipping bot creation - no credential ID")
        return None
    
    print("\n" + "="*70)
    print("🤖 STEP 2: Creating Demo Trading Bot")
    print("="*70)
    
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # High-performing pairs
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-Token": session_token
    }
    
    payload = {
        "credentialId": credential_id,
        "botId": f"demo_bot_{int(time.time())}",
        "name": "Demo Trading Bot",
        "symbols": symbols,
        "strategy": strategy,
        "enabled": True,
        "riskPerTrade": 15,        # 15% risk per trade (crypto-optimized)
        "maxDailyLoss": 50,        # Stop if lose 50UFSDT per day
        "profitLock": 40,          # Lock in at 40 USDT daily profit
        "basePositionSize": 1.0,
        "displayCurrency": "USDT"
    }
    
    print(f"\n📨 Creating bot with:")
    print(f"   Strategy: {strategy}")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Risk per trade: {payload['riskPerTrade']}%")
    print(f"   Daily loss limit: ${payload['maxDailyLoss']}")
    print(f"   Status: DEMO MODE ({'Testnet' if 'DEMO' in credential_id.upper() else 'Spot'})")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/bot/create",
            headers=headers,
            json=payload,
            timeout=60  # Bot creation may take time
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("\n✅ BOT CREATED SUCCESSFULLY!\n")
            print(json.dumps(result, indent=2))
            
            bot_id = result.get('botId')
            balance = result.get('balance', 0)
            
            print(f"\n🎯 Bot Details:")
            print(f"   Bot ID: {bot_id}")
            print(f"   Account Balance: ${balance:.2f}")
            print(f"   Status: {result.get('status', 'STARTING')}")
            print(f"   Mode: {result.get('mode', 'demo')}")
            
            return bot_id
        else:
            print("\n❌ BOT CREATION FAILED!\n")
            print(json.dumps(response.json(), indent=2))
            return None
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out - bot creation took too long")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


# ==================== STEP 3: CHECK BOT STATUS ====================
def get_bot_status(session_token: str, bot_id: str):
    """Get current status and performance of a bot"""
    
    if not bot_id:
        return
    
    print("\n" + "="*70)
    print("📈 STEP 3: Checking Bot Status")
    print("="*70)
    
    headers = {
        "Content-Type": "application/json",
        "X-Session-Token": session_token
    }
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/bot/status",
            headers=headers,
            params={"bot_id": bot_id},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            bots = result.get('bots', []) if isinstance(result, dict) else []
            bot = bots[0] if bots else None
            if bot:
                print("\n✅ BOT STATUS:\n")
                print(json.dumps(bot, indent=2))
            else:
                print("\n⚠️ Bot status endpoint returned no matching bot yet")
        else:
            print(f"\n⚠️ Status endpoint returned {response.status_code}")
            
    except Exception as e:
        print(f"\n⚠️ Could not fetch bot status: {e}")


# ==================== MAIN EXECUTION ====================
def main():
    """Run the complete test flow"""
    
    print("\n" + "="*70)
    print("🚀 ZWESTA TRADER - BINANCE BOT CREATION FLOW")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().isoformat()}")
    print(f"🌐 Backend: {BACKEND_URL}")
    
    _load_dotenv_if_available()

    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        print(f"✅ Backend is running")
    except:
        print(f"\n❌ ERROR: Backend not running at {BACKEND_URL}")
        print("   Make sure your backend server is running on port 9000")
        return

    session_token = _get_latest_active_session_token(TARGET_USER_ID)
    if not session_token:
        print("\n❌ No active session token found for test user.")
        print("   Please login once in the app/backend, then rerun this script.")
        return

    cred = _get_latest_binance_credentials(TARGET_USER_ID)
    if not cred or not cred.get('api_key') or not cred.get('api_secret'):
        print("\n❌ Could not load active Binance credentials for test user.")
        return
    
    # STEP 1: Test connection
    print("\n⏳ Waiting 2 seconds before test...")
    time.sleep(2)
    
    credential_id, balance = test_binance_connection(
        session_token=session_token,
        api_key=cred['api_key'],
        api_secret=cred['api_secret'],
        is_live=bool(cred.get('is_live', False)),
        market=cred.get('market', 'spot')
    )
    
    if not credential_id:
        print("\n❌ Cannot proceed without valid Binance credential")
        return
    
    # STEP 2: Create demo bot
    print("\n⏳ Waiting 3 seconds before bot creation...")
    time.sleep(3)
    
    bot_id = create_demo_bot(
        session_token=session_token,
        credential_id=credential_id,
        symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
        strategy="Momentum Trading"
    )
    
    if not bot_id:
        print("\n❌ Bot creation failed")
        return
    
    # STEP 3: Check bot status
    print("\n⏳ Waiting 5 seconds for bot to start trading...")
    time.sleep(5)
    
    get_bot_status(session_token, bot_id)
    
    # SUMMARY
    print("\n" + "="*70)
    print("✅ COMPLETE!")
    print("="*70)
    print(f"\n📝 Summary:")
    print(f"   ✓ Binance connection tested")
    print(f"   ✓ Credential ID: {credential_id}")
    print(f"   ✓ Account balance: ${balance:.2f}")
    print(f"   ✓ Demo bot created: {bot_id}")
    print(f"   ✓ Bot is now actively trading on: BTCUSDT, ETHUSDT, SOLUSDT")
    print(f"\n💡 Next steps:")
    print(f"   1. Check bot dashboard for live trading updates")
    print(f"   2. Monitor daily P&L on the Fleet page")
    print(f"   3. Edit risk settings if needed (risk per trade, daily loss limit)")
    print(f"\n🔗 API Endpoints:")
    print(f"   - Get bot status: GET /api/bot/status?bot_id={bot_id}")
    print(f"   - Stop bot: POST /api/bot/{bot_id}/stop")
    print(f"   - Get trades: GET /api/bot/trades?bot_id={bot_id}")
    print(f"\n⏰ Completed at: {datetime.now().isoformat()}\n")


if __name__ == "__main__":
    main()
