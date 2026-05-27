#!/usr/bin/env python3
"""Directly inspect runtime_state JSON for all bots"""
import sqlite3
import json

DB_PATH = r'C:\backend\zwesta_trading.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT bot_id, name, runtime_state FROM user_bots WHERE enabled = 1")
bots = cur.fetchall()

print("=" * 80)
print("RAW RUNTIME_STATE FROM DATABASE")
print("=" * 80)

for bot_id, name, runtime_state in bots:
    print(f"\n🤖 {bot_id} ({name})")
    print(f"   Raw JSON length: {len(runtime_state or '')}")
    
    if runtime_state:
        rs = json.loads(runtime_state)
        symbols = rs.get('symbols', [])
        signal_threshold = rs.get('signalThreshold', 'NOT SET')
        strategy_version = rs.get('strategyVersion', 'NOT SET')
        last_optimized = rs.get('lastOptimized', 'NOT SET')
        
        print(f"   Symbols: {symbols}")
        print(f"   Signal Threshold: {signal_threshold}")
        print(f"   Strategy Version: {strategy_version}")
        print(f"   Last Optimized: {last_optimized}")

conn.close()
print("\n" + "=" * 80)
