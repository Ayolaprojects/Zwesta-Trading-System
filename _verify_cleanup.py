#!/usr/bin/env python3
"""Quick bot count verification"""

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

cursor.execute("""
    SELECT COUNT(*) as total_bots,
           COUNT(CASE WHEN enabled = true THEN 1 END) as enabled,
           COUNT(CASE WHEN status = 'active' THEN 1 END) as active,
           COUNT(CASE WHEN status = 'STOPPED' OR status = 'stopped' THEN 1 END) as stopped
    FROM user_bots
""")
stats = cursor.fetchone()

print("✓ SYSTEM CLEAN - Bot Count After Cleanup:")
print(f"  Total bots: {stats['total_bots']}")
print(f"  Enabled: {stats['enabled']}")
print(f"  Active: {stats['active']}")
print(f"  Stopped: {stats['stopped']}")

if stats['stopped'] == 0:
    print("\n✓ No disabled/stopped bots remain!")
else:
    print(f"\n⚠️  {stats['stopped']} stopped bots still present")

conn.close()
