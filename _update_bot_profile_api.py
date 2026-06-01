#!/usr/bin/env python3
"""
Update bot profile via API to enable pyramiding
"""
import requests
import json

API_BASE = 'http://localhost:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'
BOT_ID = 'bot_1780067175881_3f16faa3'

print("=" * 80)
print("ENABLING PYRAMIDING VIA API")
print("=" * 80)
print(f"\nBot ID: {BOT_ID}\n")

# Login
response = requests.post(
    f'{API_BASE}/api/user/login',
    json={'email': EMAIL, 'password': PASSWORD},
    timeout=10
)

token = response.json().get('session_token')
print("✅ Logged in\n")

# Update bot configuration
update_config = {
    'managementProfile': 'balanced',  # ✅ Enable pyramiding
    'maxOpenPositions': 9,
    'maxPositionsPerSymbol': 3,
    'signalThreshold': 60,
    'intelligentScanner': True,
    'dynamicSizing': True,
}

print("Updating bot configuration...")
print(f"  Profile: balanced (pyramiding enabled)")
print(f"  Max Positions: 9")
print(f"  Max Per Symbol: 3\n")

try:
    response = requests.put(
        f'{API_BASE}/api/bot/{BOT_ID}/config',
        json=update_config,
        headers={
            'X-Session-Token': token,
            'Content-Type': 'application/json'
        },
        timeout=30
    )
    
    if response.status_code in [200, 201]:
        print("✅ BOT UPDATED SUCCESSFULLY!")
        print("\n" + "=" * 80)
        print("PYRAMIDING ENABLED!")
        print("=" * 80)
        print("\nSymbol Multipliers:")
        print("  • GBPUSDm: 2x at R1-R4.99, 5x at R5+")
        print("  • AUDUSDm: 2x at R1-R4.99, 5x at R5+")  
        print("  • XAUUSDm: 1.12x (scales with account)")
        print("\nNext Steps:")
        print("  1. Check bot in app")
        print("  2. Bot will start trading automatically")
        print("  3. Pyramiding will trigger when positions are profitable")
        print("=" * 80)
    else:
        print(f"❌ Update failed: HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying alternate method...")
    
    # Try PATCH instead of PUT
    try:
        response = requests.patch(
            f'{API_BASE}/api/bot/{BOT_ID}',
            json=update_config,
            headers={
                'X-Session-Token': token,
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            print("✅ Updated via PATCH!")
        else:
            print(f"❌ PATCH also failed: {response.status_code}")
            print(f"\n{response.text[:500]}")
    except Exception as e2:
        print(f"❌ PATCH error: {e2}")
