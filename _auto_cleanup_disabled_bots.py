#!/usr/bin/env python3
"""
Auto-cleanup disabled/stopped bots
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
print("CLEANUP: Removing disabled/stopped bots")
print("=" * 70)

# Find disabled/stopped bots
cursor.execute(
    """SELECT bot_id FROM user_bots 
       WHERE enabled = false OR status = 'STOPPED' OR status = 'stopped'
       ORDER BY created_at DESC"""
)
disabled_bots = cursor.fetchall()

if not disabled_bots:
    print("\n✓ No disabled bots to remove")
    conn.close()
    exit(0)

print(f"\nRemoving {len(disabled_bots)} bot(s)...\n")

deleted_count = 0
for bot in disabled_bots:
    bot_id = bot['bot_id']
    try:
        # Delete related records first
        cursor.execute("DELETE FROM trades WHERE bot_id = %s", (bot_id,))
        cursor.execute("DELETE FROM bot_credentials WHERE bot_id = %s", (bot_id,))
        cursor.execute("DELETE FROM bot_monitoring WHERE bot_id = %s", (bot_id,))
        cursor.execute("DELETE FROM user_bots WHERE bot_id = %s", (bot_id,))
        
        print(f"✓ Deleted: {bot_id}")
        deleted_count += 1
    except Exception as e:
        print(f"❌ Error deleting {bot_id}: {e}")

conn.commit()

print("\n" + "=" * 70)
print(f"✓ CLEANUP COMPLETE - {deleted_count} bot(s) removed")
print("=" * 70)
print("\nDatabase is now clean:")
print("  • Removed disabled/stopped bots")
print("  • Removed associated trade records")
print("  • Ready for new bot creation")

conn.close()
