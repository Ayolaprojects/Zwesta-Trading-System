#!/usr/bin/env python3
"""
Create GBPUSDm Bot with Pyramiding & Profit Protection Enabled
- 0.01 lot base entry (R128.38 fixed)
- Pyramiding multipliers: 2x at R1-R4.99, 5x at R5+
- Profit protection enabled
- Balanced profile (NOT small_account)
"""
import sys
import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\zwesta-trader\zwesta_trader.db'

# Configuration
USER_ID = 'user_1780064508001'  # Your user ID
CREDENTIAL_ID = None  # We'll find it automatically

BOT_CONFIG = {
    'name': 'GBP Pyramid Bot',
    'broker': 'Exness',
    'symbols': ['GBPUSDm'],
    'strategy': 'Trend Following',
    
    # PROFILE - CRITICAL: Must be "balanced" or "beginner" for pyramiding
    'managementProfile': 'balanced',  # ✅ Enables pyramiding
    'riskProfile': 'moderate',
    
    # BASE TRADE AMOUNT
    'tradeAmount': 128.38,  # R128.38 fixed (0.01 lot base)
    'effectiveTradeAmount': 128.38,
    
    # POSITION SIZING
    'fixedTradeVolume': 0.01,  # 0.01 lot base entrance
    'basePositionSizeMultiplier': 1.0,
    
    # RISK MANAGEMENT
    'maxOpenPositions': 3,  # Allow room for pyramid adds
    'maxPositionsPerSymbol': 3,  # 1 base + 2 adds
    'maxDailyLoss': 50.0,
    'maxDrawdownPercent': 15.0,
    
    # SIGNAL & ENTRY
    'signalThreshold': 60,
    'minRiskRewardRatio': 1.5,
    
    # PROFIT PROTECTION - ENABLED
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
    
    # PYRAMIDING - ENABLED (Will work because profile is "balanced")
    # Pyramiding config is handled by backend based on profile
    # GBPUSD gets: 2x multiplier at R1-R4.99, 5x at R5+
    
    # STATUS
    'enabled': True,
    'status': 'active',
    'is_live': True,
}

def find_exness_credential(conn):
    """Find active Exness credential for the user"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT credential_id, account_number, server, is_live
        FROM broker_credentials
        WHERE user_id = ? AND broker_name = 'Exness' AND is_active = 1
        ORDER BY is_live DESC, created_at DESC
        LIMIT 1
    """, (USER_ID,))
    
    row = cursor.fetchone()
    if row:
        return {
            'credential_id': row[0],
            'account_number': row[1],
            'server': row[2],
            'is_live': row[3]
        }
    return None

def create_bot():
    """Create the bot in database"""
    print("=" * 80)
    print("Creating GBPUSDm Pyramiding Bot")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Find credential
    print("\n[1/4] Finding Exness credential...")
    cred = find_exness_credential(conn)
    
    if not cred:
        print("❌ No Exness credential found for user.")
        print("\nPlease add Exness credentials first:")
        print("  1. Open app → Accounts → Add Broker")
        print("  2. Select Exness")
        print("  3. Enter your account details")
        conn.close()
        return False
    
    print(f"✅ Using credential: {cred['credential_id']}")
    print(f"   Account: {cred['account_number']}")
    print(f"   Server: {cred['server']}")
    print(f"   Type: {'LIVE' if cred['is_live'] else 'DEMO'}")
    
    # Create bot ID
    bot_id = f"bot_{int(datetime.now().timestamp() * 1000)}"
    
    # Prepare runtime state
    runtime_state = {
        **BOT_CONFIG,
        'botId': bot_id,
        'broker': 'Exness',
        'brokerAccountId': cred['account_number'],
        'credentialId': cred['credential_id'],
        'accountBalance': 0.0,
        'accountEquity': 0.0,
        'totalProfit': 0.0,
        'dailyProfit': 0.0,
        'peakProfit': 0.0,
        'maxDrawdown': 0.0,
        'totalTrades': 0,
        'winningTrades': 0,
        'open_positions': {},
        'tradeHistory': [],
        'profitHistory': [],
        'dailyProfits': {},
        'created_at': datetime.now().isoformat(),
    }
    
    # Insert bot
    print(f"\n[2/4] Creating bot {bot_id}...")
    try:
        cursor.execute("""
            INSERT INTO user_bots (
                bot_id, user_id, name, strategy, status, enabled,
                broker_account_id, symbols, is_live,
                runtime_state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bot_id,
            USER_ID,
            BOT_CONFIG['name'],
            BOT_CONFIG['strategy'],
            BOT_CONFIG['status'],
            1 if BOT_CONFIG['enabled'] else 0,
            cred['account_number'],
            json.dumps(BOT_CONFIG['symbols']),
            1 if cred['is_live'] else 0,
            json.dumps(runtime_state),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        print(f"✅ Bot created in database")
    except Exception as e:
        print(f"❌ Failed to create bot: {e}")
        conn.close()
        return False
    
    # Link bot to credential
    print(f"\n[3/4] Linking bot to credentials...")
    try:
        cursor.execute("""
            INSERT INTO bot_credentials (bot_id, credential_id, user_id, created_at)
            VALUES (?, ?, ?, ?)
        """, (bot_id, cred['credential_id'], USER_ID, datetime.now().isoformat()))
        print(f"✅ Bot linked to credentials")
    except Exception as e:
        print(f"⚠️  Warning: Could not link credentials: {e}")
    
    conn.commit()
    conn.close()
    
    # Print summary
    print(f"\n[4/4] Bot Configuration Summary")
    print("=" * 80)
    print(f"Bot ID: {bot_id}")
    print(f"Name: {BOT_CONFIG['name']}")
    print(f"Symbol: GBPUSDm")
    print(f"Broker: Exness ({cred['account_number']})")
    print(f"Type: {'LIVE' if cred['is_live'] else 'DEMO'}")
    print()
    print("📊 PYRAMIDING CONFIGURATION:")
    print(f"   Management Profile: {BOT_CONFIG['managementProfile']} ✅ (Pyramiding ENABLED)")
    print(f"   Base Entry: 0.01 lots (R128.38)")
    print(f"   Pyramid Multipliers:")
    print(f"      • At R1.00-R4.99 profit: 2x multiplier (adds 0.02 lots)")
    print(f"      • At R5.00+ profit: 5x multiplier (adds 0.05 lots)")
    print(f"   Max Positions: {BOT_CONFIG['maxPositionsPerSymbol']} (1 base + 2 adds)")
    print()
    print("🛡️  PROFIT PROTECTION:")
    print(f"   Enabled: ✅")
    print(f"   Activation: R{BOT_CONFIG['profitProtection']['activationMinProfit']:.2f}")
    print(f"   Breakeven Lock: ✅ (at 50% of profit target)")
    print(f"   Peak Lock: {int(BOT_CONFIG['profitProtection']['peakProfitHardLockShare'] * 100)}% of peak profit")
    print(f"   Retrace Close: {BOT_CONFIG['profitProtection']['retraceClosePercent']}% drawdown from peak")
    print()
    print("⚙️  RISK SETTINGS:")
    print(f"   Max Daily Loss: R{BOT_CONFIG['maxDailyLoss']:.2f}")
    print(f"   Max Drawdown: {BOT_CONFIG['maxDrawdownPercent']}%")
    print(f"   Signal Threshold: {BOT_CONFIG['signalThreshold']}")
    print(f"   Min R:R Ratio: {BOT_CONFIG['minRiskRewardRatio']}")
    print("=" * 80)
    print()
    print("✅ BOT CREATED SUCCESSFULLY!")
    print()
    print("Next Steps:")
    print("  1. Restart the backend: python multi_broker_backend_updated.py")
    print("  2. Bot will start trading automatically")
    print("  3. Monitor in the app: Dashboard → Bots")
    print()
    print("⚠️  IMPORTANT:")
    print("  • This bot is configured for PYRAMIDING")
    print("  • Pyramiding will add positions when:")
    print("    ✓ Parent position is profitable (>= R1.00)")
    print("    ✓ New strong signal arrives (>= 61/100)")
    print("    ✓ Market continues in same direction")
    print("  • Maximum 3 positions per symbol (1 base + 2 adds)")
    print()
    
    return True

if __name__ == '__main__':
    success = create_bot()
    sys.exit(0 if success else 1)
