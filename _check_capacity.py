"""
Check current multi-user capacity and scaling readiness
"""
import sqlite3

db_path = 'C:/backend/zwesta_trading.db'

try:
    db = sqlite3.connect(db_path)
    c = db.cursor()

    # Count unique users
    c.execute("SELECT COUNT(DISTINCT user_id) FROM broker_credentials WHERE user_id IS NOT NULL")
    user_count = c.fetchone()[0]

    # Count credentials
    c.execute("SELECT COUNT(*) FROM broker_credentials")
    cred_count = c.fetchone()[0]

    # Count active bots
    c.execute("SELECT COUNT(*) FROM user_bots WHERE enabled=1")
    active_bot_count = c.fetchone()[0]

    # Count total bots
    c.execute("SELECT COUNT(*) FROM user_bots")
    total_bot_count = c.fetchone()[0]

    # List all credentials
    c.execute("""
        SELECT account_number, server, is_live, mt5_terminal_path 
        FROM broker_credentials
        ORDER BY is_live DESC, account_number
    """)
    creds = c.fetchall()

    # Check for shared vs dedicated terminals
    shared_terminal_count = sum(1 for c in creds if not c[3])  # mt5_terminal_path is NULL
    dedicated_terminal_count = len(creds) - shared_terminal_count

    print()
    print("=" * 70)
    print("🚀 MULTI-USER CAPACITY REPORT")
    print("=" * 70)
    print()
    
    print("📊 CURRENT STATUS:")
    print(f"   👥 Unique Users:           {user_count}")
    print(f"   🔑 Broker Credentials:     {cred_count}")
    print(f"   🤖 Active Bots:            {active_bot_count}")
    print(f"   📋 Total Bots (all time):  {total_bot_count}")
    print()
    
    print("🖥️  TERMINAL ARCHITECTURE:")
    print(f"   Shared Terminal Users:     {shared_terminal_count}")
    print(f"   Dedicated Terminal Users:  {dedicated_terminal_count}")
    print()
    
    # Capacity assessment
    OPTIMAL_SHARED_CAPACITY = 10
    remaining = max(0, OPTIMAL_SHARED_CAPACITY - active_bot_count)
    usage_pct = (active_bot_count / OPTIMAL_SHARED_CAPACITY) * 100
    
    print("📈 CAPACITY ANALYSIS:")
    print(f"   Current Usage:             {active_bot_count}/{OPTIMAL_SHARED_CAPACITY} bots ({usage_pct:.0f}%)")
    print(f"   Remaining Capacity:        {remaining} bots")
    print()
    
    if usage_pct < 50:
        status = "✅ EXCELLENT - Plenty of capacity available"
        recommendation = "You can add 5+ more users without any issues"
    elif usage_pct < 80:
        status = "✅ GOOD - Operating within optimal range"
        recommendation = "Monitor trade execution times as you add more users"
    elif usage_pct < 100:
        status = "⚠️  NEAR CAPACITY - Approaching recommended limit"
        recommendation = "Consider multi-terminal setup for next 10+ users"
    else:
        status = "⚠️  OVER CAPACITY - May experience switching delays"
        recommendation = "UPGRADE TO MULTI-TERMINAL MODE recommended"
    
    print(f"   Status:                    {status}")
    print(f"   Recommendation:            {recommendation}")
    print()
    
    print("=" * 70)
    print("📋 BROKER CREDENTIALS DETAIL")
    print("=" * 70)
    
    if not creds:
        print("   (No broker credentials found)")
    else:
        for i, (acc, srv, live, path) in enumerate(creds, 1):
            mode = "🟢 LIVE" if live else "🔵 DEMO"
            terminal = path if path else "SHARED (C:\\Program Files\\MetaTrader 5 EXNESS\\)"
            
            print(f"\n   [{i}] Account: {acc}")
            print(f"       Server:   {srv}")
            print(f"       Mode:     {mode}")
            print(f"       Terminal: {terminal}")
    
    print()
    print("=" * 70)
    print("💡 SCALING OPTIONS")
    print("=" * 70)
    print()
    print("OPTION 1: Continue with Shared Terminal (Recommended for ≤10 users)")
    print("   ✅ No manual setup required")
    print("   ✅ Add users via app frontend in seconds")
    print("   ✅ Zero infrastructure changes needed")
    print("   ⚠️  3-5 second account switching delay per trade")
    print()
    print("OPTION 2: Upgrade to Multi-Terminal (For 20+ users)")
    print("   ✅ True parallel trading (no switching delay)")
    print("   ✅ Each user gets dedicated terminal")
    print("   ⚠️  Requires manual MT5 installation per user/group")
    print("   ⚠️  Higher VPS resource usage (RAM/CPU)")
    print()
    print("RECOMMENDED: Start with Option 1, upgrade to Option 2 only if you")
    print("             see trade execution delays >15 seconds with 10+ bots")
    print()
    print("=" * 70)
    print("📖 For detailed scaling guide, see: MULTI_USER_SCALING_GUIDE.md")
    print("=" * 70)
    print()

    db.close()

except Exception as e:
    print(f"❌ Error: {e}")
    print("   Make sure backend database exists at C:/backend/zwesta_trading.db")
