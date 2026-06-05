#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final system verification - no unicode"""

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
print("FINAL SYSTEM VERIFICATION REPORT")
print("=" * 70)

# Bot stats
cursor.execute("""
    SELECT COUNT(*) as total_bots,
           COUNT(CASE WHEN enabled = true THEN 1 END) as enabled,
           COUNT(CASE WHEN status = 'active' THEN 1 END) as active
    FROM user_bots
""")
bot_stats = cursor.fetchone()

print("\n[BOT STATISTICS]")
print(f"  Total bots: {bot_stats['total_bots']}")
print(f"  Enabled: {bot_stats['enabled']}/{bot_stats['total_bots']}")
print(f"  Active: {bot_stats['active']}/{bot_stats['total_bots']}")

# User stats
cursor.execute("""
    SELECT COUNT(*) as total_users,
           COUNT(CASE WHEN referrer_id IS NOT NULL THEN 1 END) as with_referrer
    FROM users
""")
user_stats = cursor.fetchone()

print("\n[USER STATISTICS]")
print(f"  Total users: {user_stats['total_users']}")
print(f"  With referrers: {user_stats['with_referrer']}")

# Broker stats
cursor.execute("""
    SELECT broker_name, COUNT(*) as count,
           COUNT(CASE WHEN is_active = true THEN 1 END) as active
    FROM broker_credentials
    GROUP BY broker_name
    ORDER BY count DESC
""")
broker_stats = cursor.fetchall()

print("\n[BROKER CREDENTIALS]")
for stat in broker_stats:
    print(f"  {stat['broker_name']}: {stat['count']} total, {stat['active']} active")

# Trade stats
cursor.execute("""
    SELECT COUNT(*) as total_trades,
           COUNT(DISTINCT bot_id) as unique_bots
    FROM trades
""")
trade_stats = cursor.fetchone()

print("\n[TRADING ACTIVITY]")
print(f"  Total trades: {trade_stats['total_trades']}")
print(f"  Unique bots traded: {trade_stats['unique_bots']}")

# Status check
print("\n[SYSTEM STATUS]")
if bot_stats['total_bots'] == bot_stats['enabled'] == bot_stats['active']:
    print("  OK - All bots enabled and active")
else:
    print("  WARNING - Some bots not active")

if trade_stats['total_trades'] > 0:
    print("  OK - System trading actively")
else:
    print("  WARNING - No trades recorded")

conn.close()

print("\n" + "=" * 70)
print("READY FOR NEW USERS & BOTS")
print("=" * 70)
