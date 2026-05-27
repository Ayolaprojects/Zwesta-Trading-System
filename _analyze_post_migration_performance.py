"""
Zwesta Trading System - Post-Migration Performance Analysis
Investigates why system is taking losses after PostgreSQL migration
Previously had 10+ straight profitable trades
"""

import os
import sys
sys.path.insert(0, r'C:\backend')

from runtime_infrastructure import (
    get_database_backend, 
    get_sqlalchemy_engine,
    using_postgres
)
from sqlalchemy import text
from datetime import datetime, timedelta

def print_header(title):
    print("\n" + "═" * 80)
    print(f"  {title}")
    print("═" * 80)

def analyze_trading_performance():
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  POST-MIGRATION TRADING PERFORMANCE ANALYSIS".center(78) + "█")
    print("█" + "  Investigating Loss Pattern After PostgreSQL Migration".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    print(f"\nAnalysis Date: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}")
    
    # Check database backend
    print_header("DATABASE STATUS")
    backend = get_database_backend()
    is_postgres = using_postgres()
    print(f"\nCurrent Database: {backend}")
    print(f"Using PostgreSQL: {is_postgres}")
    
    if not is_postgres:
        print("\n⚠️  WARNING: Not using PostgreSQL! Expected postgres mode.")
        return
    
    # Connect to database
    try:
        engine = get_sqlalchemy_engine()
        conn = engine.connect()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Check bot configurations
    print_header("BOT CONFIGURATION COMPARISON")
    
    try:
        # Get all active bots
        query = text("""
            SELECT 
                bot_id,
                user_id,
                broker,
                is_active,
                volatility_profile,
                max_hold_seconds,
                trade_amount,
                stop_loss_pct,
                take_profit_pct,
                max_active_positions,
                profit_protection_enabled,
                retain_profit_pct,
                created_at
            FROM bot_configs
            WHERE is_active = TRUE
            ORDER BY bot_id
        """)
        
        result = conn.execute(query)
        bots = result.fetchall()
        
        print(f"\n📊 Active Bots: {len(bots)}")
        print()
        
        for bot in bots:
            print(f"Bot ID {bot[0]} (User {bot[1]}, {bot[2]}):")
            print(f"  ├─ Volatility Profile:     {bot[4]}")
            print(f"  ├─ Max Hold Time:          {bot[5]} seconds")
            print(f"  ├─ Trade Amount:           {bot[6]}")
            print(f"  ├─ Stop Loss:              {bot[7]}%")
            print(f"  ├─ Take Profit:            {bot[8]}%")
            print(f"  ├─ Max Positions:          {bot[9]}")
            print(f"  ├─ Profit Protection:      {bot[10]}")
            print(f"  └─ Profit Retention:       {bot[11]}%")
            print()
        
    except Exception as e:
        print(f"❌ Error querying bot configs: {e}")
    
    # Check recent trades/positions
    print_header("RECENT TRADING ACTIVITY")
    
    try:
        # Check if pxbt_positions table exists
        query = text("""
            SELECT position_id, bot_id, symbol, position_type, volume, 
                   open_price, current_price, profit, status, open_time, close_time
            FROM pxbt_positions
            WHERE open_time > :since
            ORDER BY open_time DESC
            LIMIT 20
        """)
        
        since = datetime.now() - timedelta(hours=24)
        result = conn.execute(query, {"since": since})
        positions = result.fetchall()
        
        print(f"\n📈 Positions in Last 24 Hours: {len(positions)}")
        print()
        
        if positions:
            profitable = sum(1 for p in positions if p[7] and p[7] > 0)
            losing = sum(1 for p in positions if p[7] and p[7] < 0)
            total_profit = sum(p[7] for p in positions if p[7])
            
            print(f"Win Rate: {profitable}/{len(positions)} = {profitable/len(positions)*100:.1f}%")
            print(f"Profitable: {profitable}")
            print(f"Losing: {losing}")
            print(f"Total P/L: R{total_profit:.2f}")
            print()
            
            print("Recent Positions:")
            for p in positions[:10]:
                status = "🟢 PROFIT" if p[7] and p[7] > 0 else "🔴 LOSS"
                print(f"  {status} Bot {p[1]} {p[2]} {p[3]} Vol:{p[4]} P/L:R{p[7]:.2f} Status:{p[8]}")
        else:
            print("⚠️  No positions found in last 24 hours")
            print()
            print("Possible reasons:")
            print("  1. Bots not executing trades")
            print("  2. Market conditions not meeting entry criteria")
            print("  3. Position data not being written to database")
            
    except Exception as e:
        print(f"⚠️  Could not query pxbt_positions table: {e}")
        print()
        print("Note: This table may not exist or may be empty after migration")
    
    # Check bot execution logs
    print_header("BOT EXECUTION STATUS")
    
    try:
        query = text("""
            SELECT bot_id, COUNT(*) as session_count, 
                   MAX(timestamp) as last_session
            FROM sessions
            WHERE timestamp > :since
            GROUP BY bot_id
            ORDER BY bot_id
        """)
        
        since = datetime.now() - timedelta(hours=24)
        result = conn.execute(query, {"since": since})
        sessions = result.fetchall()
        
        print(f"\n🔄 Bot Sessions in Last 24 Hours:")
        print()
        
        if sessions:
            for s in sessions:
                last_session = s[2].strftime('%Y-%m-%d %H:%M:%S') if s[2] else 'Never'
                print(f"  Bot {s[0]}: {s[1]} sessions | Last: {last_session}")
        else:
            print("  ⚠️  No bot sessions recorded in last 24 hours")
            print()
            print("  Possible reasons:")
            print("  1. Bots are paused/stopped")
            print("  2. Backend not running")
            print("  3. Session logging not working")
    
    except Exception as e:
        print(f"❌ Error querying sessions: {e}")
    
    # Check for configuration changes
    print_header("POTENTIAL ISSUES IDENTIFIED")
    
    print()
    print("🔍 Common Issues After Database Migration:")
    print()
    print("1️⃣  BOT PARAMETERS RESET:")
    print("   ├─ Check if volatility_profile changed")
    print("   ├─ Verify stop_loss_pct and take_profit_pct are correct")
    print("   ├─ Confirm max_hold_seconds is appropriate")
    print("   └─ ACTION: Compare with pre-migration settings")
    print()
    print("2️⃣  MARKET VOLATILITY CHANGES:")
    print("   ├─ Market conditions may have changed")
    print("   ├─ Previous 10+ wins may have been during favorable conditions")
    print("   ├─ Current losses may be due to market, not migration")
    print("   └─ ACTION: Check if other traders also experiencing losses")
    print()
    print("3️⃣  TIMING/EXECUTION ISSUES:")
    print("   ├─ PostgreSQL may have different response times")
    print("   ├─ Slight delays could affect entry/exit timing")
    print("   ├─ Check if orders are filling at expected prices")
    print("   └─ ACTION: Review order execution logs")
    print()
    print("4️⃣  PROFIT PROTECTION SETTINGS:")
    print("   ├─ Check if profit_protection_enabled changed")
    print("   ├─ Verify retain_profit_pct is correct")
    print("   ├─ May be closing winning trades too early")
    print("   └─ ACTION: Review profit protection logic")
    print()
    print("5️⃣  STATISTICAL VARIANCE (Normal):")
    print("   ├─ 10+ wins followed by losses is NORMAL variance")
    print("   ├─ No trading strategy wins 100% of the time")
    print("   ├─ Even 70% win rate has losing streaks")
    print("   └─ ACTION: Track over 50+ trades for true performance")
    
    # Recommendations
    print_header("RECOMMENDED ACTIONS")
    
    print()
    print("✅ IMMEDIATE CHECKS:")
    print()
    print("1. Review bot configurations in PostgreSQL vs SQLite backup")
    print("2. Check if volatility_profile or stop_loss settings changed")
    print("3. Verify bots are executing trades (check backend logs)")
    print("4. Monitor next 10-20 trades to establish new baseline")
    print("5. Check broker account balance and margin requirements")
    print()
    print("📊 PERFORMANCE TRACKING:")
    print()
    print("Required Metrics:")
    print("├─ Win Rate:              Target 55-70%")
    print("├─ Average Win:           Track R value")
    print("├─ Average Loss:          Should be < Average Win")
    print("├─ Profit Factor:         Target 1.5+ (gross profit / gross loss)")
    print("└─ Max Drawdown:          Monitor for risk management")
    print()
    print("⚠️  IMPORTANT:")
    print("Database migration does NOT change trading logic or algorithms.")
    print("If bot code unchanged, performance difference is likely:")
    print("  1. Market conditions changed")
    print("  2. Configuration parameters changed during migration")
    print("  3. Normal statistical variance (losing streak)")
    print()
    print("Sample size matters: Need 50+ trades to judge true performance.")
    
    conn.close()
    print()

if __name__ == "__main__":
    try:
        analyze_trading_performance()
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
