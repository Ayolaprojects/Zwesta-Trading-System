#!/usr/bin/env python3
"""
Test Exness bot creation and trade execution.
"""
import requests
import json
import time

BASE_URL = "http://localhost:9000"

def test_exness_bot_creation():
    """Test creating an Exness bot."""
    
    # First, create/login user
    print("=" * 60)
    print("STEP 1: Login/Create User")
    print("=" * 60)
    
    login_resp = requests.post(
        f"{BASE_URL}/api/user/login",
        json={"email": "exness-test@zwesta.com", "password": "test123"},
        timeout=10
    )
    print(f"Login response: {login_resp.status_code}")
    print(json.dumps(login_resp.json(), indent=2))
    
    if login_resp.status_code != 200:
        # Try signup
        print("\nUser doesn't exist, attempting signup...")
        signup_resp = requests.post(
            f"{BASE_URL}/api/user/signup",
            json={
                "email": "exness-test@zwesta.com",
                "password": "test123",
                "name": "Exness Test"
            },
            timeout=10
        )
        print(f"Signup response: {signup_resp.status_code}")
        print(json.dumps(signup_resp.json(), indent=2))
        
        # Try login again
        login_resp = requests.post(
            f"{BASE_URL}/api/user/login",
            json={"email": "exness-test@zwesta.com", "password": "test123"},
            timeout=10
        )
        print(f"Login retry: {login_resp.status_code}")
    
    if login_resp.status_code != 200:
        print("❌ Login failed")
        return False
    
    user_data = login_resp.json()
    user_id = user_data.get("user_id")
    token = user_data.get("token")
    print(f"✅ Logged in as {user_id}")
    
    # Step 2: Add Exness credentials
    print("\n" + "=" * 60)
    print("STEP 2: Add Exness Credentials")
    print("=" * 60)
    
    cred_resp = requests.post(
        f"{BASE_URL}/api/credentials/add",
        json={
            "broker": "exness",
            "login": "12345678",  # Replace with test credentials
            "password": "password",  # Replace with test password
            "server": "Exness-MT5 Live",
            "account_type": "live"
        },
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )
    print(f"Credentials response: {cred_resp.status_code}")
    print(json.dumps(cred_resp.json(), indent=2))
    
    if cred_resp.status_code != 200:
        print("❌ Failed to add credentials")
        return False
    
    cred_id = cred_resp.json().get("credential_id")
    print(f"✅ Credentials added: {cred_id}")
    
    # Step 3: Create bot
    print("\n" + "=" * 60)
    print("STEP 3: Create Exness Bot")
    print("=" * 60)
    
    bot_config = {
        "name": "Exness Test Bot",
        "credential_id": cred_id,
        "broker": "exness",
        "symbols": ["EURUSD", "GBPUSD"],
        "entry_mode": "signal",
        "signal_threshold": 60,
        "max_positions": 1,
        "risk_percent": 2.0,
        "pyramiding": False
    }
    
    bot_resp = requests.post(
        f"{BASE_URL}/api/bot/create",
        json=bot_config,
        headers={"Authorization": f"Bearer {token}"},
        timeout=45
    )
    print(f"Bot creation response: {bot_resp.status_code}")
    resp_json = bot_resp.json()
    print(json.dumps(resp_json, indent=2))
    
    if bot_resp.status_code != 200:
        print("❌ Bot creation failed")
        return False
    
    bot_id = resp_json.get("bot_id")
    print(f"✅ Bot created: {bot_id}")
    
    # Step 4: Check bot status and signals
    print("\n" + "=" * 60)
    print("STEP 4: Check Bot Status & Signals")
    print("=" * 60)
    
    time.sleep(5)
    
    status_resp = requests.get(
        f"{BASE_URL}/api/bot/{bot_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    print(f"Bot status response: {status_resp.status_code}")
    status_data = status_resp.json()
    print(json.dumps(status_data, indent=2))
    
    # Check for signals
    signals_resp = requests.get(
        f"{BASE_URL}/api/bot/{bot_id}/signals",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    print(f"\nSignals response: {signals_resp.status_code}")
    signals_data = signals_resp.json()
    print(json.dumps(signals_data, indent=2)[:500])
    
    print("\n✅✅ EXNESS BOT CREATION TEST PASSED")
    return True

if __name__ == "__main__":
    try:
        success = test_exness_bot_creation()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
