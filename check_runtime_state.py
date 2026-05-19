#!/usr/bin/env python3
import sqlite3
import json

conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cursor = conn.cursor()

print('🔍 CHECKING BOT RUNTIME STATE FOR SIGNAL THRESHOLDS')
print('='*50)

cursor.execute('SELECT bot_id, name, runtime_state FROM user_bots WHERE enabled = 1')
bots = cursor.fetchall()

for bot_id, name, runtime_state in bots:
    print(f'\n🤖 {name} ({bot_id[:20]}...):')
    if runtime_state:
        try:
            state = json.loads(runtime_state)
            # Look for signal-related settings
            if 'signal_threshold' in state:
                print(f'   Signal Threshold: {state["signal_threshold"]}')
            if 'signalThreshold' in state:
                print(f'   Signal Threshold: {state["signalThreshold"]}')
            if 'threshold' in state:
                print(f'   Threshold: {state["threshold"]}')
            # Show all keys containing 'signal' or 'threshold' or 'management'
            signal_keys = [k for k in state.keys() if 'signal' in k.lower() or 'threshold' in k.lower() or 'management' in k.lower()]
            if signal_keys:
                print(f'   Signal/Management keys found: {signal_keys}')
                for key in signal_keys:
                    print(f'     {key}: {state[key]}')
            else:
                print('   No signal settings in runtime_state')
        except json.JSONDecodeError:
            print('   Invalid JSON in runtime_state')
    else:
        print('   No runtime_state data')

conn.close()