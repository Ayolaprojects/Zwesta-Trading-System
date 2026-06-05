#!/usr/bin/env python3
"""
Verify new user registration and broker credential setup
Tests Binance and Exness onboarding workflows
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
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
print("USER REGISTRATION & BROKER SETUP VERIFICATION")
print("=" * 70)

# 1. Check users table structure
print("\n1. Checking users table structure...")
try:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    required_cols = ['id', 'email', 'name', 'created_at']
    found_cols = {col['column_name'] for col in columns}
    
    missing = set(required_cols) - found_cols
    if missing:
        print(f"   ❌ Missing columns: {missing}")
    else:
        print(f"   ✓ All required columns present")
        for col in required_cols:
            print(f"     - {col}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Check broker_credentials table structure
print("\n2. Checking broker_credentials table structure...")
try:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'broker_credentials'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    required_cols = ['credential_id', 'user_id', 'broker_name', 'account_number', 
                     'is_live', 'is_active', 'created_at']
    found_cols = {col['column_name'] for col in columns}
    
    missing = set(required_cols) - found_cols
    if missing:
        print(f"   ⚠️  Missing columns: {missing}")
        print(f"   Available: {', '.join(sorted(found_cols))}")
    else:
        print(f"   ✓ All credential columns present")
        for col in required_cols:
            print(f"     - {col}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Check user statistics
print("\n3. Checking user statistics...")
try:
    cursor.execute("""
        SELECT COUNT(*) as total_users,
               COUNT(CASE WHEN created_at::timestamp > NOW() - INTERVAL '7 days' THEN 1 END) as new_this_week,
               COUNT(CASE WHEN created_at::timestamp > NOW() - INTERVAL '1 day' THEN 1 END) as new_today
        FROM users
    """)
    user_stats = cursor.fetchone()
    print(f"   Total users: {user_stats['total_users']}")
    print(f"   New this week: {user_stats['new_this_week']}")
    print(f"   New today: {user_stats['new_today']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 4. Check broker credential statistics
print("\n4. Checking broker credentials by broker...")
try:
    cursor.execute("""
        SELECT broker_name, COUNT(*) as count, 
               COUNT(CASE WHEN is_active = true THEN 1 END) as active
        FROM broker_credentials
        GROUP BY broker_name
        ORDER BY count DESC
    """)
    broker_stats = cursor.fetchall()
    
    print(f"   Broker Credentials:")
    if broker_stats:
        for stat in broker_stats:
            status = "✓" if stat['active'] > 0 else "⚠️"
            print(f"   {status} {stat['broker_name']}: {stat['count']} total, {stat['active']} active")
        
        # Check for both Binance and Exness
        brokers = {stat['broker_name'].lower() for stat in broker_stats}
        if 'binance' not in brokers and 'exness' not in brokers:
            print(f"\n   ❌ WARNING: No Binance or Exness credentials found!")
            print(f"      New users must set up credentials for at least one broker")
    else:
        print(f"   ❌ No broker credentials found")
        print(f"      New users cannot create bots without credentials")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 5. Check if users have credentials
print("\n5. Checking user credential setup...")
try:
    cursor.execute("""
        SELECT u.user_id, u.email, COUNT(bc.credential_id) as cred_count,
               STRING_AGG(DISTINCT bc.broker_name, ', ') as brokers
        FROM users u
        LEFT JOIN broker_credentials bc ON u.user_id = bc.user_id
        GROUP BY u.user_id, u.email
        ORDER BY u.created_at DESC
        LIMIT 10
    """)
    user_creds = cursor.fetchall()
    
    print(f"   Recent users and their credentials:")
    for user in user_creds:
        status = "✓" if user['cred_count'] > 0 else "❌"
        brokers = user['brokers'] or "NONE"
        print(f"   {status} {user['email']}: {user['cred_count']} credentials ({brokers})")
        if user['cred_count'] == 0:
            print(f"      → User {user['user_id']} needs broker setup")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 6. Check for registration workflow issues
print("\n6. Checking registration workflow...")
try:
    # Check if there are users without any credentials (potential issue)
    cursor.execute("""
        SELECT COUNT(*) as users_without_credentials
        FROM users u
        WHERE NOT EXISTS (
            SELECT 1 FROM broker_credentials bc WHERE bc.user_id = u.user_id
        )
        AND u.created_at IS NOT NULL
    """)
    result = cursor.fetchone()
    
    if result['users_without_credentials'] > 0:
        print(f"   ⚠️  {result['users_without_credentials']} users without credentials!")
        print(f"      These users cannot create bots")
        print(f"      ACTION: Guide users to add broker credentials")
    else:
        print(f"   ✓ All users have broker credentials")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print("\n" + "=" * 70)
print("USER REGISTRATION STATUS")
print("=" * 70)
print("\nREQUIREMENTS FOR NEW USERS:")
print("1. ✓ Create user account (register endpoint)")
print("2. ✓ Add Binance credentials (API key + secret)")
print("3. ✓ Add Exness credentials (MT5 login + password)")
print("4. ✓ Create bot from either broker")
print("5. ✓ Start trading")

print("\nRECOMMENDED ACTIONS:")
print("• Guide new users to set up at least ONE broker credential")
print("• Offer both Binance and Exness as options during signup")
print("• Validate credentials before allowing bot creation")
print("• Provide testing mode (DEMO) for new users first")

conn.close()
