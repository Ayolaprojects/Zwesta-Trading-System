#!/usr/bin/env python3
"""
Test Binance server time sync
"""

import requests
import time

# Test Binance server time endpoint
print("Testing Binance server time sync...")

try:
    # Get Binance server time
    response = requests.get("https://api.binance.com/api/v3/time", timeout=10)
    if response.status_code == 200:
        server_time = response.json()['serverTime']
        local_time = int(time.time() * 1000)
        offset = server_time - local_time

        print(f"✅ Binance server time: {server_time}")
        print(f"❌ Local system time: {local_time}")
        print(f"📊 Time offset: {offset} ms ({offset/1000:.1f} seconds)")

        if abs(offset) > 5000:  # More than 5 seconds difference
            print("❌ CRITICAL: Time difference too large (>5 seconds)")
            print("This will cause Binance API authentication failures")
        else:
            print("✅ Time difference acceptable (<5 seconds)")
    else:
        print(f"❌ Failed to get server time: {response.status_code}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\nIf the offset is too large, the VPS system clock needs to be fixed.")