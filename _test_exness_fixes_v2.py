#!/usr/bin/env python3
"""
Test Exness credential verification after pool and timeout fixes.
"""
import requests
import json
import time
import sys

# Replace with your Exness test credentials
EXNESS_LOGIN = "12345678"  # Replace with test login
EXNESS_PASSWORD = "password"  # Replace with test password
EXNESS_SERVER = "Exness-MT5 Live"  # or "Exness-MT5 Demo"

def test_exness_verify():
    """Test Exness quick credential verification endpoint."""
    url = "http://localhost:9000/api/exness/verify"
    payload = {
        "login": EXNESS_LOGIN,
        "password": EXNESS_PASSWORD,
        "server": EXNESS_SERVER,
    }
    
    print(f"Testing Exness credential verification...")
    print(f"  Login: {EXNESS_LOGIN}")
    print(f"  Server: {EXNESS_SERVER}")
    print(f"  URL: {url}")
    print(f"  Expected timeout: ~25-35 seconds (was timing out at 20s)")
    print()
    
    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=60)
        elapsed = time.time() - start
        
        print(f"✅ Response received in {elapsed:.1f}s")
        print(f"  Status: {resp.status_code}")
        print(f"  Body: {resp.text[:500]}")
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                print(f"✅✅ EXNESS VERIFICATION PASSED!")
                return True
            else:
                print(f"⚠️  Verification failed: {data.get('error', 'unknown error')}")
                return False
        else:
            print(f"❌ HTTP {resp.status_code}")
            return False
    except requests.Timeout:
        elapsed = time.time() - start
        print(f"❌ TIMEOUT after {elapsed:.1f}s - FIX NOT WORKING")
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ Error after {elapsed:.1f}s: {e}")
        return False

if __name__ == "__main__":
    if EXNESS_LOGIN == "12345678":
        print("❌ Please set EXNESS_LOGIN and EXNESS_PASSWORD at the top of this script")
        sys.exit(1)
    
    success = test_exness_verify()
    sys.exit(0 if success else 1)
