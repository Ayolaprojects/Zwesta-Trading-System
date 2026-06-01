#!/usr/bin/env python3
"""
Force update bot profile to 'balanced' to enable pyramiding
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\zwesta-trader\zwesta_trader.db'

BOT_ID = 'bot_1780067175881_3f16faa3'

print("=" * 80)
print(f"UPDATING BOT PROFILE TO ENABLE PYRAMIDING")
print("=" * 80)
print(f"\nBot ID: {BOT_ID}\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get current runtime state
cursor.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (BOT_ID,))
row = cursor.fetchone()

if not row:
    print(f"❌ Bot not found: {BOT_ID}")
    conn.close()
    exit(1)

runtime_state = json.loads(row[0]) if row[0] else {}

print("Current Settings:")
print(f"  Management Profile: {runtime_state.get('managementProfile', 'not set')}")
print(f"  Max Open Positions: {runtime_state.get('maxOpenPositions', 'not set')}")
print(f"  Max Per Symbol: {runtime_state.get('maxPositionsPerSymbol', 'not set')}")

# Update to balanced profile
runtime_state['managementProfile'] = 'balanced'
runtime_state['maxOpenPositions'] = 9
runtime_state['maxPositionsPerSymbol'] = 3
runtime_state['signalThreshold'] = 60
runtime_state['intelligentScanner'] = True
runtime_state['dynamicSizing'] = True

# Remove small account guards
if 'managementMode' in runtime_state:
    runtime_state['managementMode'] = 'assisted'

# Update in database
cursor.execute("""
    UPDATE user_bots
    SET runtime_state = ?, updated_at = ?
    WHERE bot_id = ?
""", (json.dumps(runtime_state), datetime.now().isoformat(), BOT_ID))

conn.commit()
conn.close()

print("\n✅ Bot Updated!")
print("\nNew Settings:")
print(f"  Management Profile: {runtime_state.get('managementProfile')} ✅")
print(f"  Max Open Positions: {runtime_state.get('maxOpenPositions')}")
print(f"  Max Per Symbol: {runtime_state.get('maxPositionsPerSymbol')}")
print("\n" + "=" * 80)
print("PYRAMIDING NOW ENABLED!")
print("=" * 80)
print("\nSymbol Multipliers:")
print("  • GBPUSDm: 2x at R1-R4.99, 5x at R5+")
print("  • AUDUSDm: 2x at R1-R4.99, 5x at R5+")
print("  • XAUUSDm: 1.12x (scales with account)")
print("\nRestart the backend for changes to take effect:")
print("  python multi_broker_backend_updated.py")
print("=" * 80)
