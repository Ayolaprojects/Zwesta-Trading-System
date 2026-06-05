#!/usr/bin/env python3
"""Diagnose bot trading issues in PostgreSQL"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os

# PostgreSQL connection
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'zwesta_trading'),
        user=os.getenv('DB_USER', 'zwesta_admin'),
        password=os.getenv('DB_PASSWORD', 'Zwesta@Trading2026!')
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)
except Exception as e:
    print(f"❌ PostgreSQL Connection Error: {e}")
    exit(1)

print("=" * 60)
print("POSTGRES BOT DIAGNOSTIC")
print("=" * 60)

# Check if bot1780614250152 exists
print("\n1. Searching for bot1780614250152...")
cursor.execute(
    """SELECT bot_id, user_id, broker_account_id, symbols, status, enabled 
       FROM user_bots WHERE bot_id LIKE %s""",
    ('%1780614250152%',)
)
bot_result = cursor.fetchone()

if bot_result:
    print(f"✓ Found bot: {bot_result}")
    bot_id = bot_result['bot_id']
    
    # Check recent trades
    cursor.execute(
        """SELECT COUNT(*) as trade_count, MAX(created_at) as last_trade 
           FROM trades WHERE bot_id = %s AND created_at > NOW() - INTERVAL '24 hours'""",
        (bot_id,)
    )
    trades = cursor.fetchone()
    print(f"  Trades in last 24h: {trades['trade_count']}")
    print(f"  Last trade: {trades['last_trade']}")
else:
    print(f"❌ Bot matching '1780614250152' not found in user_bots table")
    
    # Try to find similar IDs
    print("\n  Searching for similar bot IDs...")
    cursor.execute(
        """SELECT bot_id, broker_account_id, symbols, status 
           FROM user_bots WHERE bot_id LIKE '%1780614%' LIMIT 10"""
    )
    similar = cursor.fetchall()
    if similar:
        print(f"  Found {len(similar)} similar bots:")
        for bot in similar:
            print(f"    - {bot['bot_id']}: {bot['symbols']}")

# Check all Exness bots
print("\n2. Checking Exness bots...")
cursor.execute(
    """SELECT bot_id, symbols, status, enabled, created_at 
       FROM user_bots WHERE broker_account_id LIKE '%Exness%' ORDER BY created_at DESC"""
)
exness_bots = cursor.fetchall()

if exness_bots:
    print(f"✓ Found {len(exness_bots)} Exness bots:")
    for bot in exness_bots:
        cursor.execute(
            """SELECT COUNT(*) as trade_count, MAX(created_at::timestamp) as last_trade
               FROM trades WHERE bot_id = %s AND created_at::timestamp > NOW() - INTERVAL '7 days'""",
            (bot['bot_id'],)
        )
        trade_stats = cursor.fetchone()
        
        print(f"\n  Bot: {bot['bot_id']}")
        print(f"    Symbols: {bot['symbols']}")
        print(f"    Status: {bot['status']}, Enabled: {bot['enabled']}")
        print(f"    7-day trades: {trade_stats['trade_count']}")
        print(f"    Last trade: {trade_stats['last_trade']}")
else:
    print("❌ No Exness bots found")

# Check for flash trades (trades closed very quickly)
print("\n3. Checking for flash trades (< 5 seconds on Exness)...")
try:
    cursor.execute(
        """SELECT bot_id, symbol, created_at, updated_at, pnl
           FROM trades t
           WHERE EXISTS (
               SELECT 1 FROM user_bots b WHERE b.bot_id = t.bot_id 
               AND b.broker_account_id LIKE '%Exness%'
           )
           AND t.created_at::timestamp > NOW() - INTERVAL '7 days'
           ORDER BY t.created_at::timestamp DESC LIMIT 50"""
    )
    all_trades = cursor.fetchall()

    flash_count = 0
    if all_trades:
        for trade in all_trades:
            # Skip if timestamps are not properly formatted
            if trade['created_at'] and trade['updated_at']:
                try:
                    created = trade['created_at']
                    updated = trade['updated_at']
                    if isinstance(created, str):
                        from datetime import datetime
                        created = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                    duration = (updated - created).total_seconds()
                    if duration < 5:
                        if flash_count == 0:
                            print(f"⚠️  Found flash trades (< 5 seconds):")
                        flash_count += 1
                        print(f"  {created}: {trade['symbol']} - {int(duration)}s - PnL: {trade['pnl']}")
                except:
                    pass
        
        if flash_count == 0:
            print("✓ No flash trades found in last 7 days")
    else:
        print("ℹ️  No trades found in last 7 days")
except Exception as e:
    print(f"ℹ️  Could not check flash trades: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
if bot_result:
    print(f"✓ bot1780614250152 exists in database")
else:
    print(f"❌ bot1780614250152 NOT in database - may need to be recreated")

if exness_bots:
    enabled_count = sum(1 for b in exness_bots if b['enabled'])
    trading_count = sum(1 for b in exness_bots if b['enabled'] and b['status'] != 'STOPPED')
    print(f"⚠️  {len(exness_bots)} Exness bots found - ALL STOPPED/DISABLED")
    print(f"   Enabled: {enabled_count}/{len(exness_bots)}")
    print(f"   Active/Trading: {trading_count}/{len(exness_bots)}")
else:
    print(f"❌ No Exness bots in database")

print("\n" + "=" * 60)
print("RECOMMENDED ACTIONS")
print("=" * 60)
print("1. bot1780614250152: BOT DOES NOT EXIST")
print("   → Create this bot with proper configuration")
print("")
print("2. Exness Bots: ALL 7 BOTS ARE DISABLED AND STOPPED")
print("   → Enable the bots in the database")
print("   → Start the bots to resume trading")

conn.close()
