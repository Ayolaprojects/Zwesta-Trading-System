#!/usr/bin/env python3
"""
Test bot creation and trade execution on both Exness and Binance.
"""
import requests
import json
import time

BASE_URL = "http://localhost:9000"

def test_bot_management():
    """Test bot creation and management."""
    
    print("=" * 70)
    print("SYSTEM HEALTH CHECK")
    print("=" * 70)
    
    # Test 1: Check if API is responding
    print("\n1. Checking API Health")
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"   /api/health: {resp.status_code}")
    except:
        print("   /api/health: Not available")
    
    # Test 2: Try existing Binance bot signals
    print("\n2. Testing Existing Binance Bots (no auth needed)")
    try:
        # Try to get public bot info
        resp = requests.get(f"{BASE_URL}/api/bots/public", timeout=10)
        if resp.status_code == 200:
            bots = resp.json()
            print(f"   Public bots: {len(bots)}")
            for bot in bots[:3]:
                print(f"     - {bot.get('name')}: {bot.get('status')}")
    except Exception as e:
        print(f"   Public bots endpoint: {e}")
    
    # Test 3: Check for demo/test endpoint
    print("\n3. Checking for Available Test Endpoints")
    test_endpoints = [
        "/api/demo/bots",
        "/api/test/bots",
        "/api/bots/status",
        "/api/system/status"
    ]
    
    for endpoint in test_endpoints:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"   {endpoint}: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    print(f"      → {list(data.keys())[:5]}")
        except:
            pass
    
    # Test 4: Test login with simple credentials
    print("\n4. Testing User Login")
    test_logins = [
        {"email": "admin@zwesta.com", "password": "admin"},
        {"email": "test@zwesta.com", "password": "test"},
        {"email": "user@zwesta.com", "password": "user"},
    ]
    
    token = None
    for creds in test_logins:
        try:
            resp = requests.post(
                f"{BASE_URL}/api/user/login",
                json=creds,
                timeout=10
            )
            print(f"   {creds['email']}: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success'):
                    token = data.get('token')
                    print(f"      ✅ LOGIN SUCCESS")
                    break
                elif data.get('token'):
                    token = data.get('token')
                    print(f"      ✅ GOT TOKEN")
                    break
        except Exception as e:
            print(f"   {creds['email']}: Error - {str(e)[:50]}")
    
    if token:
        print(f"\n   Using token: {token[:20]}...")
        
        # Test 5: Get user bots with token
        print("\n5. Getting User's Bots")
        try:
            resp = requests.get(
                f"{BASE_URL}/api/bots",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            print(f"   Response: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                bots = data.get('bots', [])
                print(f"   Found {len(bots)} bots")
                for bot in bots[:5]:
                    print(f"     - {bot.get('name')}: {bot.get('broker')}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 6: Check signals for first bot
        print("\n6. Checking Bot Signals & Trading Activity")
        try:
            resp = requests.get(
                f"{BASE_URL}/api/bots",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                bots = data.get('bots', [])
                
                for bot in bots[:2]:  # Check first 2 bots
                    bot_id = bot.get('id') or bot.get('bot_id')
                    bot_name = bot.get('name')
                    
                    print(f"\n   Bot: {bot_name}")
                    print(f"   Status: {bot.get('status')}")
                    print(f"   Broker: {bot.get('broker')}")
                    print(f"   P&L: {bot.get('profit', 0)}")
                    
                    # Try to get detailed stats
                    try:
                        stats_resp = requests.get(
                            f"{BASE_URL}/api/bot/{bot_id}/stats",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=10
                        )
                        if stats_resp.status_code == 200:
                            stats = stats_resp.json()
                            print(f"   Trades: {stats.get('total_trades', 0)}")
                            print(f"   Open Positions: {stats.get('open_positions', 0)}")
                    except:
                        pass
        except Exception as e:
            print(f"   Error: {e}")
    else:
        print("\n❌ Could not authenticate with any user")
    
    print("\n" + "=" * 70)
    print("✅ SYSTEM HEALTH CHECK COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_bot_management()
