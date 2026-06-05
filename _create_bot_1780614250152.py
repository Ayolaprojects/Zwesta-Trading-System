#!/usr/bin/env python3
"""
Script to create bot1780614250152

Run this after providing the required bot configuration details.
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

print("=" * 60)
print("BOT CREATION HELPER: bot1780614250152")
print("=" * 60)

# First, check if it exists
cursor.execute(
    "SELECT * FROM user_bots WHERE bot_id = %s",
    ('bot1780614250152',)
)
existing = cursor.fetchone()
if existing:
    print("✓ Bot already exists!")
    print(f"  Status: {existing['status']}")
    print(f"  Enabled: {existing['enabled']}")
    conn.close()
    exit(0)

print("\nTo create bot1780614250152, please provide:")
print("-" * 60)

# Get user input
user_id_input = input("User ID (UUID or email): ").strip()
broker_account = input("Broker Account ID (e.g., Exness_123456): ").strip()
symbols = input("Symbols (comma-separated, e.g., XAUUSDm,GBPUSDm): ").strip()
strategy = input("Strategy (default: Trend Following): ").strip() or "Trend Following"
initial_capital = input("Initial Capital (default: 500): ").strip() or "500"

# Get user ID from email if provided
cursor.execute(
    "SELECT id FROM users WHERE email = %s OR id = %s LIMIT 1",
    (user_id_input, user_id_input)
)
user_result = cursor.fetchone()
if not user_result:
    print(f"❌ User not found: {user_id_input}")
    conn.close()
    exit(1)

user_id = user_result['id']
print(f"\n✓ Found user: {user_id}")

# Default runtime state
runtime_state = {
    "copyTradingSourceBotId": None,
    "equityTrendHistory": [],
    "displayCurrency": "ZAR",
    "basePositionSize": 1.0,
    "copyTradingLastResolvedAt": None,
    "intelligentScanner": False,
    "dailyEquityTargetPercent": 0.0,
    "copyTradingSourceMode": "manual",
    "effectiveSignalThreshold": 66,
    "promotionReadyAt": None,
    "profitHistory": [],
    "strategy": strategy,
    "tradeAmountAdaptation": {
        "timestamp": datetime.now().isoformat(),
        "state": "manual_override",
        "multiplier": 1.0,
        "scannerCapitalMultiplier": 1.0,
        "baseTradeAmount": 100.0,
        "adjustedTradeAmount": 100.0,
        "reason": "initial setup"
    }
}

# Create bot
print("\nCreating bot...")
now = datetime.now().isoformat()

cursor.execute(
    """INSERT INTO user_bots 
    (bot_id, user_id, name, strategy, status, enabled, daily_profit, total_profit,
     broker_account_id, symbols, created_at, updated_at, runtime_state)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
    (
        'bot1780614250152',
        user_id,
        f'Bot - {strategy}',
        strategy,
        'active',
        True,
        0.0,
        0.0,
        broker_account,
        symbols,
        now,
        now,
        json.dumps(runtime_state)
    )
)

conn.commit()

print("\n" + "=" * 60)
print("✓ BOT CREATED SUCCESSFULLY")
print("=" * 60)
print(f"\nBot ID: bot1780614250152")
print(f"User ID: {user_id}")
print(f"Broker Account: {broker_account}")
print(f"Symbols: {symbols}")
print(f"Strategy: {strategy}")
print(f"Status: active")
print(f"Enabled: Yes")

print("\nNext steps:")
print("1. Restart bot launchers")
print("2. Monitor for trading activity")

conn.close()
