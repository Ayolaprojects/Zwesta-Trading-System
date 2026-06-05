#!/usr/bin/env python3
"""
Show cleanup plan for disabled bots
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
print("CLEANUP PLAN - Disabled/Stopped Bots")
print("=" * 70)

# Find disabled/stopped bots
cursor.execute(
    """SELECT bot_id, user_id, broker_account_id, symbols, status, enabled, created_at
       FROM user_bots 
       WHERE enabled = false OR status = 'STOPPED' OR status = 'stopped'
       ORDER BY created_at DESC"""
)
disabled_bots = cursor.fetchall()

if not disabled_bots:
    print("\n✓ No disabled/stopped bots to clean up!")
    conn.close()
    exit(0)

print(f"\nFound {len(disabled_bots)} disabled/stopped bot(s) to remove:\n")

total_trades = 0
total_size = 0
for i, bot in enumerate(disabled_bots, 1):
    # Count trades for this bot
    cursor.execute(
        "SELECT COUNT(*) as count FROM trades WHERE bot_id = %s",
        (bot['bot_id'],)
    )
    trade_count = cursor.fetchone()['count']
    total_trades += trade_count
    
    print(f"{i}. Bot ID: {bot['bot_id']}")
    print(f"   Status: {bot['status']}, Enabled: {bot['enabled']}")
    print(f"   Broker: {bot['broker_account_id']}")
    print(f"   Symbols: {bot['symbols']}")
    print(f"   Created: {bot['created_at']}")
    print(f"   Trades: {trade_count}")
    print()

print("=" * 70)
print("CLEANUP IMPACT")
print("=" * 70)
print(f"\nWill delete:")
print(f"  • {len(disabled_bots)} bot(s)")
print(f"  • {total_trades} trade record(s)")
print(f"\nSpace freed: ~{(total_trades * 500 // 1024)} KB (approx)")

conn.close()
