#!/usr/bin/env python3
"""
Test Binance bot creation on VPS backend
"""

import requests
import json
import time
from datetime import datetime

# VPS backend URL
BASE_URL = "http://148.113.5.39:9000"

# Test user credentials
TEST_EMAIL = "zwexman@gmail.com"
TEST_PASSWORD = "your_password_here"  # Replace with actual password

print("🔐 Logging in to get fresh session token...")

try:
    login_response = requests.post(
        f"{BASE_URL}/api/user/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        },
        timeout=30
    )

    if login_response.status_code == 200:
        login_data = login_response.json()
        if login_data.get("success"):
            SESSION_TOKEN = login_data.get("session_token")
            print("✅ Login successful, got fresh session token")
        else:
            print(f"❌ Login failed: {login_data.get('error')}")
            exit(1)
    else:
        print(f"❌ Login HTTP error: {login_response.status_code}")
        exit(1)

except Exception as e:
    print(f"❌ Login error: {e}")
    exit(1)

# Update headers with fresh token
headers = {
    "Content-Type": "application/json",
    "X-Session-Token": SESSION_TOKEN
}

print("=" * 80)
print("🔍 TESTING BINANCE BOT CREATION ON VPS")
print("=" * 80)
print()

headers = {
    "Content-Type": "application/json",
    "X-Session-Token": SESSION_TOKEN
}

# Test Binance bot creation
print("🤖 Creating Binance DEMO bot...")
start_time = time.time()

try:
    response = requests.post(
        f"{BASE_URL}/api/bot/create",
        json={
            "botId": f"test_binance_demo_{int(datetime.now().timestamp())}",
            "symbol": "BTCUSDT",
            "strategy": "Trend Following",
            "riskPerTrade": 1.0,
            "timeframe": "1H",
            "is_live": False,
            "volatility_filter_enabled": False,
            "broker": "Binance",
            "account": "demo",  # Binance demo doesn't need account number
            "mode": "demo",
            "leverage": 1
        },
        headers=headers,
        timeout=60  # Increased timeout
    )

    elapsed = time.time() - start_time
    print(f"⏱️  Request took {elapsed:.2f} seconds")

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            bot_id = data.get("botId")
            print(f"✅ SUCCESS: Binance demo bot created!")
            print(f"   Bot ID: {bot_id}")
            print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"⚠️  Bot creation failed (but API responded)")
            print(f"   Error: {data.get('error', 'Unknown')}")
            print(f"   Response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Raw response: {response.text[:500]}")

except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f"⏱️  TIMEOUT after {elapsed:.2f} seconds")
    print("❌ Bot creation timed out - likely timestamp sync issue")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"⏱️  Failed after {elapsed:.2f} seconds")
    print(f"❌ Error: {e}")

print()
print("If this times out, run 'w32tm /resync' on the VPS to sync the clock.")