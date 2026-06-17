#!/usr/bin/env python3
import sqlite3
import json

db = sqlite3.connect('zwesta_trading.db')
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Get all bots
cursor.execute("SELECT * FROM user_bots LIMIT 15")
bots = cursor.fetchall()

print(f"\nFound {len(bots)} active bots:\n")
print(f"{'Bot ID':<12} {'Symbol':<12} {'Broker':<10} {'Risk%':>6} {'Signal':>6} {'Max Loss':>10} {'Profile':<12}")
print("-" * 80)

for bot in bots:
    print(f"{str(bot['botId']):<12} {str(bot.get('symbol', 'N/A')):<12} {str(bot.get('broker', 'N/A')):<10} "
          f"{str(bot.get('riskPerTrade', 'N/A')):>6} {str(bot.get('signalThreshold', 'N/A')):>6} "
          f"{str(bot.get('maxDailyLoss', 'N/A')):>10} {str(bot.get('managementProfile', 'N/A')):<12}")

db.close()
