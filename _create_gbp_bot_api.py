#!/usr/bin/env python3
"""
Create GBPUSDm Bot via API with Pyramiding & Profit Protection
- Uses Flask API (proper method)
- 0.01 lot base entry
- Pyramiding enabled (balanced profile)
- Profit protection enabled
"""
import requests
import json
import sys

API_BASE = 'http://localhost:9000'  # Local backend

# Login credentials
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'

def login():
    """Login and get session token"""
    print("[1/3] Logging in...")
    try:
        response = requests.post(
            f'{API_BASE}/api/user/login',
            json={'email': EMAIL, 'password': PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('session_token')
            user_id = data.get('user_id')
            print(f"✅ Logged in as {EMAIL}")
            print(f"   User ID: {user_id}")
            return token, user_id
        else:
            print(f"❌ Login failed: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None, None

def get_credentials(token):
    """Get Exness credentials"""
    print("\n[2/3] Finding Exness credentials...")
    try:
        response = requests.get(
            f'{API_BASE}/api/broker/credentials',
            headers={'X-Session-Token': token},
            timeout=10
        )
        
        if response.status_code == 200:
            creds = response.json().get('credentials', [])
            exness_creds = [c for c in creds if 'Exness' in c.get('broker_name', '')]
            
            if exness_creds:
                cred = exness_creds[0]
                print(f"✅ Found Exness credential")
                print(f"   Credential ID: {cred.get('credential_id')}")
                print(f"   Account: {cred.get('account_number')}")
                print(f"   Server: {cred.get('server')}")
                return cred.get('credential_id')
            else:
                print("❌ No Exness credentials found")
                print("\nAvailable credentials:")
                for c in creds:
                    print(f"  - {c.get('broker_name')}: {c.get('account_number')}")
                return None
        else:
            print(f"❌ Failed to get credentials: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting credentials: {e}")
        return None

def create_bot(token, credential_id):
    """Create the bot"""
    print("\n[3/3] Creating GBPUSDm Pyramiding Bot...")
    
    bot_config = {
        'credentialId': credential_id,
        'name': 'GBP Pyramid Bot',
        'strategy': 'Trend Following',
        'symbols': ['GBPUSDm'],
        
        # CRITICAL: Use "balanced" profile for pyramiding
        'managementProfile': 'balanced',  # ✅ Enables pyramiding
        'riskProfile': 'moderate',
        
        # Trade amount (0.01 lot = R128.38)
        'tradeAmount': 128.38,
        'fixedTradeVolume': 0.01,
        
        # Position limits
        'maxOpenPositions': 3,  # Allow pyramid positions
        'maxPositionsPerSymbol': 3,  # 1 base + 2 adds
        
        # Risk management
        'maxDailyLoss': 50.0,
        'maxDrawdownPercent': 15.0,
        'signalThreshold': 60,
        'minRiskRewardRatio': 1.5,
        
        # Profit protection
        'profitProtection': {
            'enabled': True,
            'activationMinProfit': 5.0,
            'activationPercent': 2.0,
            'retraceClosePercent': 35.0,
            'breakEvenLockEnabled': True,
            'breakEvenBufferProfit': 0.5,
            'breakEvenActivationShare': 0.5,
            'peakProfitHardLockShare': 0.9,
            'volatilityBucket': 'medium',
        },
    }
    
    try:
        response = requests.post(
            f'{API_BASE}/api/bot/create',
            json=bot_config,
            headers={
                'X-Session-Token': token,
                'Content-Type': 'application/json'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                bot_id = result.get('bot_id') or result.get('botId')
                print(f"\n✅ BOT CREATED SUCCESSFULLY!")
                print(f"\nBot ID: {bot_id}")
                print("\n" + "=" * 80)
                print("CONFIGURATION SUMMARY")
                print("=" * 80)
                print(f"Name: {bot_config['name']}")
                print(f"Symbol: GBPUSDm")
                print(f"Strategy: {bot_config['strategy']}")
                print()
                print("📊 PYRAMIDING:")
                print(f"   Profile: {bot_config['managementProfile']} ✅ (ENABLED)")
                print(f"   Base Entry: 0.01 lots (R128.38)")
                print(f"   Multipliers:")
                print(f"      • R1-R4.99: 2x (adds 0.02 lots)")
                print(f"      • R5+: 5x (adds 0.05 lots)")
                print(f"   Max Positions: {bot_config['maxPositionsPerSymbol']}")
                print()
                print("🛡️  PROFIT PROTECTION:")
                print(f"   Enabled: ✅")
                print(f"   Activation: R5.00")
                print(f"   Breakeven Lock: ✅")
                print(f"   Peak Lock: 90%")
                print(f"   Retrace Close: 35%")
                print()
                print("⚙️  RISK MANAGEMENT:")
                print(f"   Max Daily Loss: R{bot_config['maxDailyLoss']}")
                print(f"   Max Drawdown: {bot_config['maxDrawdownPercent']}%")
                print(f"   Signal Threshold: {bot_config['signalThreshold']}")
                print("=" * 80)
                print()
                print("Next Steps:")
                print("  1. Check bot in app: Dashboard → Bots")
                print("  2. Bot will auto-start on backend restart")
                print("  3. Monitor positions and pyramiding activity")
                print()
                return True
            else:
                print(f"❌ Bot creation failed: {result.get('error') or result}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Error creating bot: {e}")
        return False

def main():
    print("=" * 80)
    print("GBPUSDm Pyramiding Bot Creator (API Method)")
    print("=" * 80)
    print()
    
    # Step 1: Login
    token, user_id = login()
    if not token:
        return False
    
    # Step 2: Get credentials
    credential_id = get_credentials(token)
    if not credential_id:
        print("\n⚠️  Please add Exness credentials first:")
        print("   1. Open Zwesta app")
        print("   2. Go to Accounts → Add Broker")
        print("   3. Select Exness")
        print("   4. Enter your MT5 account details")
        return False
    
    # Step 3: Create bot
    success = create_bot(token, credential_id)
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
