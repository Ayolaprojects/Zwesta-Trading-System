#!/usr/bin/env python3
"""Check current symbol configuration for all active bots"""
import sqlite3
import json

DB_PATH = r'C:\backend\zwesta_trading.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT bot_id, name, runtime_state FROM user_bots WHERE enabled = 1")
bots = cur.fetchall()

print("=" * 80)
print("CURRENT BOT SYMBOL CONFIGURATION")
print("=" * 80)

for bot_id, name, runtime_state in bots:
    rs = json.loads(runtime_state or '{}')
    symbols = rs.get('symbols', [])
    
    print(f"\n🤖 {bot_id}")
    print(f"   Name: {name}")
    print(f"   Symbols: {symbols}")
    if symbols:
        print(f"   First symbol: {symbols[0]} {'✅ (GBPUSDm - profitable)' if symbols[0] == 'GBPUSDm' else '❌'}")

conn.close()
print("\n" + "=" * 80)
