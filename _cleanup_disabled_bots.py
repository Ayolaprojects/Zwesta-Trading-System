#!/usr/bin/env python3
"""
Cleanup disabled/stopped bots and ensure system integrity
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'zwesta_trading'),
    user=os.getenv('DB_USER', 'zwesta_admin'),
    password=os.getenv('DB_PASSWORD', 'Zwesta@Trading2026!')
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 70)
print("BOT CLEANUP - Remove disabled/non-trading bots")
print("=" * 70)

# Find disabled bots with no trades
cursor.execute(
    """SELECT bot_id, broker_account_id, symbols, status, enabled, created_at
       FROM user_bots 
       WHERE enabled = false OR status = 'STOPPED'
       ORDER BY created_at DESC"""
)
disabled_bots = cursor.fetchall()

if not disabled_bots:
    print("\n✓ No disabled bots found")
    conn.close()
    exit(0)

print(f"\nFound {len(disabled_bots)} disabled/stopped bots:\n")
for i, bot in enumerate(disabled_bots, 1):
    print(f"{i}. {bot['bot_id']}")
    print(f"   Broker: {bot['broker_account_id']}")
    print(f"   Symbols: {bot['symbols']}")
    print(f"   Status: {bot['status']}, Enabled: {bot['enabled']}")

# Ask for confirmation
response = input("\n⚠️  Delete these bots? (yes/no): ").strip().lower()
if response != 'yes':
    print("❌ Cancelled")
    conn.close()
    exit(0)

# Delete bots
deleted_count = 0
for bot in disabled_bots:
    try:
        # Delete related records
        cursor.execute("DELETE FROM trades WHERE bot_id = %s", (bot['bot_id'],))
        cursor.execute("DELETE FROM bot_credentials WHERE bot_id = %s", (bot['bot_id'],))
        cursor.execute("DELETE FROM user_bots WHERE bot_id = %s", (bot['bot_id'],))
        deleted_count += 1
        print(f"✓ Deleted: {bot['bot_id']}")
    except Exception as e:
        print(f"❌ Error deleting {bot['bot_id']}: {e}")

conn.commit()

print("\n" + "=" * 70)
print(f"✓ CLEANUP COMPLETE - {deleted_count} bots deleted")
print("=" * 70)

conn.close()
