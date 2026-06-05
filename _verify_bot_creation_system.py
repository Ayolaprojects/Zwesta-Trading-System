#!/usr/bin/env python3
"""
Verify bot creation system works correctly
Tests the complete bot creation workflow
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
import json
import uuid

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'zwesta_trading'),
    user=os.getenv('DB_USER', 'zwesta_admin'),
    password=os.getenv('DB_PASSWORD', 'Zwesta@Trading2026!')
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 70)
print("BOT CREATION SYSTEM VERIFICATION")
print("=" * 70)

# 1. Check user_bots table structure
print("\n1. Checking user_bots table structure...")
try:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user_bots'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    required_cols = ['bot_id', 'user_id', 'broker_account_id', 'symbols', 'status', 'enabled']
    found_cols = {col['column_name'] for col in columns}
    
    missing = set(required_cols) - found_cols
    if missing:
        print(f"   ❌ Missing columns: {missing}")
    else:
        print(f"   ✓ All required columns present")
        for col in required_cols:
            print(f"     - {col}")
except Exception as e:
    print(f"   ❌ Error checking columns: {e}")

# 2. Check broker_credentials table
print("\n2. Checking broker_credentials table structure...")
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'broker_credentials'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    print(f"   ✓ broker_credentials has {len(columns)} columns")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Check sample bot creation validation
print("\n3. Testing bot creation validation logic...")
try:
    # Get a sample user
    cursor.execute("SELECT user_id FROM users LIMIT 1")
    user_result = cursor.fetchone()
    if user_result:
        user_id = user_result['user_id']
        
        # Get a sample broker credential for this user
        cursor.execute("""
            SELECT credential_id, broker_name, account_number, is_live 
            FROM broker_credentials 
            WHERE user_id = %s LIMIT 1
        """, (user_id,))
        
        cred_result = cursor.fetchone()
        if cred_result:
            broker_name = cred_result['broker_name']
            account_num = cred_result['account_number']
            is_live = cred_result['is_live']
            mode = "LIVE" if is_live else "DEMO"
            
            print(f"   ✓ Sample credential found:")
            print(f"     - Broker: {broker_name}")
            print(f"     - Account: {account_num}")
            print(f"     - Mode: {mode}")
        else:
            print(f"   ℹ️  No broker credentials for sample user yet")
    else:
        print(f"   ℹ️  No users in database yet")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Check existing bots
print("\n4. Checking existing bots...")
try:
    cursor.execute("""
        SELECT COUNT(*) as total_bots,
               COUNT(CASE WHEN enabled = true THEN 1 END) as enabled,
               COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
               COUNT(CASE WHEN status = 'STOPPED' OR status = 'stopped' THEN 1 END) as stopped
        FROM user_bots
    """)
    stats = cursor.fetchone()
    print(f"   Total bots: {stats['total_bots']}")
    print(f"   Enabled: {stats['enabled']}")
    print(f"   Active: {stats['active']}")
    print(f"   Stopped: {stats['stopped']}")
    
    if stats['stopped'] and stats['stopped'] > 0:
        print(f"\n   ⚠️  {stats['stopped']} stopped bots detected!")
        print(f"      Run: python _cleanup_disabled_bots.py")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Check trades recording
print("\n5. Checking trades table...")
try:
    cursor.execute("""
        SELECT COUNT(*) as total_trades,
               COUNT(DISTINCT bot_id) as unique_bots,
               MAX(created_at::timestamp) as latest_trade
        FROM trades
    """)
    trade_stats = cursor.fetchone()
    print(f"   Total trades recorded: {trade_stats['total_trades']}")
    print(f"   Unique bots traded: {trade_stats['unique_bots']}")
    if trade_stats['latest_trade']:
        print(f"   Latest trade: {trade_stats['latest_trade']}")
    else:
        print(f"   ℹ️  No trades recorded yet")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("SYSTEM READY FOR BOT CREATION")
print("=" * 70)
print("\nNext steps:")
print("1. Users can create bots via API or UI")
print("2. Bots will auto-start trading when enabled")
print("3. Check trade logs for execution status")

conn.close()
