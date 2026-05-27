"""
Bulk create multiple users with Exness accounts and bots programmatically
Demonstrates how to scale to 10+ users via backend API
"""
import requests
import json
from typing import List, Dict

BASE_URL = 'http://localhost:9000'

# Configure your users here
USERS = [
    {
        'email': 'trader1@example.com',
        'password': 'SecurePass123!',
        'name': 'Trader One',
        'exness_account': '123456789',
        'exness_password': 'ExnessPass1@',
        'exness_server': 'Exness-MT5Trial9',  # Demo server
        'is_live': False,  # Set True for live trading
    },
    {
        'email': 'trader2@example.com',
        'password': 'SecurePass456!',
        'name': 'Trader Two',
        'exness_account': '987654321',
        'exness_password': 'ExnessPass2@',
        'exness_server': 'Exness-MT5Real27',  # Live server
        'is_live': True,
    },
    # Add more users here...
    # {
    #     'email': 'trader3@example.com',
    #     'password': 'SecurePass789!',
    #     'name': 'Trader Three',
    #     'exness_account': '555666777',
    #     'exness_password': 'ExnessPass3@',
    #     'exness_server': 'Exness-MT5Real27',
    #     'is_live': True,
    # },
]

def create_user_and_bot(user_data: Dict) -> bool:
    """
    Create user account, add Exness broker credentials, and create trading bot
    
    Returns True if successful, False otherwise
    """
    
    print(f"\n{'='*70}")
    print(f"Creating: {user_data['email']}")
    print('='*70)
    
    try:
        # Step 1: Register user account
        print("  [1/3] Registering user account...")
        resp = requests.post(f'{BASE_URL}/api/auth/register', json={
            'email': user_data['email'],
            'password': user_data['password'],
            'name': user_data['name'],
        }, timeout=10)
        
        result = resp.json()
        if not result.get('success'):
            print(f"  ❌ Failed to register user: {result.get('message', 'Unknown error')}")
            return False
        
        user_id = result['user']['userId']
        session_token = result['session_token']
        print(f"  ✅ User registered successfully (ID: {user_id})")
        
        # Step 2: Add Exness broker credentials
        print("  [2/3] Adding Exness broker credentials...")
        resp = requests.post(f'{BASE_URL}/api/broker/credentials', 
            headers={'X-Session-Token': session_token},
            json={
                'broker_name': 'Exness',
                'account_number': str(user_data['exness_account']),
                'password': user_data['exness_password'],
                'server': user_data['exness_server'],
                'is_live': user_data['is_live'],
                'mt5_terminal_path': None,  # ⚠️ NULL = auto-use shared terminal
            },
            timeout=10
        )
        
        result = resp.json()
        if not result.get('success'):
            print(f"  ❌ Failed to add credentials: {result.get('message', 'Unknown error')}")
            return False
        
        credential_id = result['credential']['credential_id']
        mode_str = "LIVE 🟢" if user_data['is_live'] else "DEMO 🔵"
        print(f"  ✅ Credentials added: Account {user_data['exness_account']} [{mode_str}]")
        print(f"     Server: {user_data['exness_server']}")
        print(f"     Terminal: SHARED (auto-detected)")
        
        # Step 3: Create trading bot
        print("  [3/3] Creating trading bot...")
        resp = requests.post(f'{BASE_URL}/api/bot/create',
            headers={'X-Session-Token': session_token},
            json={
                'broker': 'Exness',
                'broker_credential_id': credential_id,
                'strategy': 'Scalping',  # Can be: Scalping, Trend Following, Mean Reversion
                'symbols': ['XAUUSDm', 'GBPUSDm', 'USTECm'],
                'tradeAmount': 100.0,
                'riskProfile': 'balanced',  # Can be: beginner, balanced, aggressive, fast_growth
                'maxOpenPositions': 3,
                'mode': 'live' if user_data['is_live'] else 'demo',
                'enabled': True,  # Start bot immediately
            },
            timeout=10
        )
        
        result = resp.json()
        if not result.get('success'):
            print(f"  ❌ Failed to create bot: {result.get('message', 'Unknown error')}")
            return False
        
        bot_id = result['bot']['bot_id']
        print(f"  ✅ Bot created: {bot_id}")
        print(f"     Strategy: Scalping")
        print(f"     Symbols: XAUUSDm, GBPUSDm, USTECm")
        print(f"     Trade Amount: R100.00")
        print(f"     Risk Profile: Balanced")
        print(f"     Status: ACTIVE ✅")
        
        print(f"\n  🎉 SUCCESS! User {user_data['email']} is ready to trade!")
        return True
        
    except requests.exceptions.Timeout:
        print(f"  ❌ Timeout connecting to backend at {BASE_URL}")
        print(f"     Make sure backend is running on port 9000")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Cannot connect to backend at {BASE_URL}")
        print(f"     Make sure backend is running: python C:/backend/multi_broker_backend_updated.py")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def main():
    """Create all users in bulk"""
    
    print("\n" + "="*70)
    print("🚀 BULK USER CREATION - MULTI-USER SCALING")
    print("="*70)
    print(f"\nBackend URL: {BASE_URL}")
    print(f"Users to create: {len(USERS)}")
    print(f"Mode: Shared Terminal (auto-detected)")
    print()
    
    # Verify backend is running
    try:
        resp = requests.get(f'{BASE_URL}/api/health', timeout=5)
        if resp.status_code != 200:
            print("⚠️  Backend health check failed - make sure backend is running!")
            print("   Start backend: cd C:\\backend && python multi_broker_backend_updated.py")
            return
        print("✅ Backend is running and healthy\n")
    except:
        print("❌ Cannot connect to backend!")
        print("   Start backend: cd C:\\backend && python multi_broker_backend_updated.py")
        return
    
    # Create all users
    success_count = 0
    failed_users = []
    
    for i, user in enumerate(USERS, 1):
        print(f"\n[{i}/{len(USERS)}] Processing {user['email']}...")
        
        if create_user_and_bot(user):
            success_count += 1
        else:
            failed_users.append(user['email'])
    
    # Summary
    print("\n" + "="*70)
    print("📊 CREATION SUMMARY")
    print("="*70)
    print(f"✅ Successful: {success_count}/{len(USERS)} users")
    print(f"❌ Failed:     {len(failed_users)}/{len(USERS)} users")
    
    if failed_users:
        print(f"\nFailed Users:")
        for email in failed_users:
            print(f"  • {email}")
    
    print()
    print("="*70)
    print("💡 NEXT STEPS")
    print("="*70)
    if success_count > 0:
        print("1. ✅ Log into app with any of the created user credentials")
        print("2. ✅ Check bot status - should show ACTIVE/RUNNING")
        print("3. ✅ Monitor trades - bots start trading immediately")
        print("4. ✅ Run capacity check: python _check_capacity.py")
    else:
        print("⚠️  No users were created successfully")
        print("   Check backend logs for errors")
        print("   Verify backend is running on port 9000")
    print()


if __name__ == '__main__':
    main()
