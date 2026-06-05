#!/usr/bin/env python3
"""Enable and start all Exness bots"""

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

print("=" * 60)
print("ENABLING AND STARTING EXNESS BOTS")
print("=" * 60)

# Get all Exness bots
cursor.execute(
    """SELECT bot_id, symbols, status, enabled FROM user_bots 
       WHERE broker_account_id LIKE '%Exness%' ORDER BY created_at DESC"""
)
exness_bots = cursor.fetchall()

if not exness_bots:
    print("❌ No Exness bots found")
    conn.close()
    exit(1)

print(f"\nFound {len(exness_bots)} Exness bots to enable:\n")

# Enable all bots
for bot in exness_bots:
    cursor.execute(
        """UPDATE user_bots SET enabled = true, status = 'active' 
           WHERE bot_id = %s""",
        (bot['bot_id'],)
    )
    print(f"✓ Enabled: {bot['bot_id']} ({bot['symbols']})")

conn.commit()

print("\n" + "=" * 60)
print("✓ ALL EXNESS BOTS ENABLED")
print("=" * 60)
print("\nNext steps:")
print("1. Restart the bot launchers/watchdogs")
print("2. Verify bots are starting to trade")
print("3. Monitor trade execution")

conn.close()
