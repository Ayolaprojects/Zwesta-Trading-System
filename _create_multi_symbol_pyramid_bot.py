#!/usr/bin/env python3
"""
Create Multi-Symbol Pyramiding Bot
Symbols: GBPUSDm, AUDUSDm, XAUUSDm (Best pyramiding symbols)
"""
import requests
import json

API_BASE = 'http://localhost:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'

print("=" * 80)
print("MULTI-SYMBOL PYRAMIDING BOT CREATOR")
print("Symbols: GBPUSDm, AUDUSDm, XAUUSDm")
print("=" * 80)
print()

# Login
print("[1/3] Logging in...")
response = requests.post(
    f'{API_BASE}/api/user/login',
    json={'email': EMAIL, 'password': PASSWORD},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json().get('session_token')
user_id = response.json().get('user_id')
print(f"✅ Logged in as {EMAIL}")
print(f"   User ID: {user_id}\n")

# Get credentials
print("[2/3] Finding Exness credentials...")
response = requests.get(
    f'{API_BASE}/api/broker/credentials',
    headers={'X-Session-Token': token},
    timeout=10
)

if response.status_code != 200:
    print(f"❌ Failed to get credentials")
    exit(1)

creds = response.json().get('credentials', [])

# Find Exness by server name (since broker_name might be empty)
exness_creds = [c for c in creds if 'Exness' in str(c.get('server', ''))]

if not exness_creds:
    print("❌ No Exness credentials found!")
    print("\nPlease add Exness credentials first:")
    print("  1. Open Zwesta app → Accounts → Add Broker")
    print("  2. Select Exness")
    print("  3. Enter your MT5 account details")
    exit(1)

# Prefer LIVE account, fallback to DEMO
exness_creds.sort(key=lambda x: x.get('is_live', False), reverse=True)

credential_id = exness_creds[0].get('credential_id')
account_number = exness_creds[0].get('account_number')
server = exness_creds[0].get('server')
is_live = exness_creds[0].get('is_live', False)

print(f"✅ Found Exness credential")
print(f"   Account: {account_number}")
print(f"   Server: {server}")
print(f"   Type: {'LIVE' if is_live else 'DEMO'}\n")

# Create bot
print("[3/3] Creating Multi-Symbol Pyramiding Bot...")

bot_config = {
    'credentialId': credential_id,
    'name': 'Multi-Symbol Pyramid Bot',
    'strategy': 'Trend Following',
    
    # BEST PYRAMIDING SYMBOLS
    'symbols': ['GBPUSDm', 'AUDUSDm', 'XAUUSDm'],
    
    # CRITICAL: balanced profile enables pyramiding
    'managementProfile': 'balanced',  # ✅ Pyramiding ENABLED
    'riskProfile': 'moderate',
    
    # Trade sizing (0.01 lot base per symbol)
    'tradeAmount': 128.38,
    'fixedTradeVolume': 0.01,
    
    # Position limits (3 symbols × 3 positions each = 9 max)
    'maxOpenPositions': 9,  # Allow all symbols to pyramid
    'maxPositionsPerSymbol': 3,  # 1 base + 2 pyramid adds per symbol
    
    # Risk management
    'maxDailyLoss': 100.0,  # Higher for multiple symbols
    'maxDrawdownPercent': 20.0,
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
    
    if response.status_code == 200 or response.status_code == 201:
        result = response.json()
        bot_id = result.get('bot_id') or result.get('botId')
        
        # Check if backend overrode to small_account
        applied_config = result.get('appliedManagementConfig', {})
        actual_profile = applied_config.get('managementProfile', bot_config['managementProfile'])
        
        if actual_profile == 'small_account':
            print(f"\n⚠️ WARNING: Backend forced 'small_account' profile!")
            print(f"   This disables pyramiding.")
            print(f"\n   Requested: {bot_config['managementProfile']}")
            print(f"   Applied: {actual_profile}")
            print(f"\n   Likely reason: Small account balance detected")
            print(f"\n   SOLUTION: Update bot profile after creation...")
            
        if result.get('success') or bot_id:
            bot_id = result.get('bot_id') or result.get('botId')
            
            print(f"\n{'=' * 80}")
            print("✅ MULTI-SYMBOL PYRAMIDING BOT CREATED!")
            print(f"{'=' * 80}")
            print(f"\nBot ID: {bot_id}")
            print(f"Name: {bot_config['name']}")
            print(f"Account: {account_number} ({server})")
            print(f"Type: {'LIVE' if is_live else 'DEMO'}")
            
            print(f"\n{'─' * 80}")
            print("📊 SYMBOLS & PYRAMIDING MULTIPLIERS:")
            print(f"{'─' * 80}")
            print("  1. GBPUSDm (Premium Forex)")
            print("     • Base: 0.01 lots (R128.38)")
            print("     • Multiplier: 2x at R1-R4.99, 5x at R5+")
            print("     • Min profit: R1.00")
            print("     • Signal: 61/100")
            print()
            print("  2. AUDUSDm (Premium Forex)")
            print("     • Base: 0.01 lots (R128.38)")
            print("     • Multiplier: 2x at R1-R4.99, 5x at R5+")
            print("     • Min profit: R1.00")
            print("     • Signal: 61/100")
            print()
            print("  3. XAUUSDm (Gold - Enhanced)")
            print("     • Base: 0.01 lots (R128.38)")
            print("     • Multiplier: 1.12x (scales with account)")
            print("     • Min profit: R1.10")
            print("     • Signal: 63.5/100")
            
            print(f"\n{'─' * 80}")
            print("⚙️ CONFIGURATION:")
            print(f"{'─' * 80}")
            print(f"  Management Profile: {bot_config['managementProfile']} ✅")
            print(f"  Max Positions: {bot_config['maxOpenPositions']} total")
            print(f"  Max Per Symbol: {bot_config['maxPositionsPerSymbol']} (1 base + 2 adds)")
            print(f"  Max Daily Loss: R{bot_config['maxDailyLoss']}")
            print(f"  Max Drawdown: {bot_config['maxDrawdownPercent']}%")
            
            print(f"\n{'─' * 80}")
            print("🛡️ PROFIT PROTECTION:")
            print(f"{'─' * 80}")
            print("  ✅ Enabled")
            print("  ✅ Breakeven lock at 50% of target")
            print("  ✅ Peak lock at 90% of peak profit")
            print("  ✅ Retrace close at 35% drawdown from peak")
            
            print(f"\n{'─' * 80}")
            print("📈 HOW PYRAMIDING WORKS:")
            print(f"{'─' * 80}")
            print("  Each symbol pyramids INDEPENDENTLY:")
            print()
            print("  Example - GBPUSDm:")
            print("    Entry: 0.01 lot SELL")
            print("    → Reaches R2.50 profit")
            print("    → New strong signal arrives")
            print("    → AUTO ADD: 0.02 lots (2x)")
            print("    → Total: 0.03 lots")
            print()
            print("    → Reaches R7.00 profit")
            print("    → Another strong signal")
            print("    → AUTO ADD: 0.05 lots (5x)")
            print("    → Total: 0.08 lots")
            print()
            print("  Same logic applies to AUD and Gold!")
            
            print(f"\n{'=' * 80}")
            print("NEXT STEPS:")
            print(f"{'=' * 80}")
            print("  1. ✅ Bot created and ready")
            print("  2. Check in app: Dashboard → Bots")
            print("  3. Bot will auto-start when backend restarts")
            print("  4. Monitor pyramiding activity per symbol")
            print()
            print("⚠️ IMPORTANT:")
            print("  • Each symbol can have up to 3 positions (1 + 2 adds)")
            print("  • Total max positions: 9 (3 symbols × 3)")
            print("  • Pyramiding triggers when profit >= R1 AND strong signal")
            print("  • GBP & AUD have the HIGHEST multipliers (5x at R5+)")
            print(f"{'=' * 80}\n")
            
        else:
            print(f"\n❌ Bot creation failed!")
            print(f"Error: {result.get('error') or result}")
            print(f"\nFull response: {json.dumps(result, indent=2)}")
    else:
        print(f"\n❌ HTTP {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
