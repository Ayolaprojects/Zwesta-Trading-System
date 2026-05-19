#!/usr/bin/env python3
"""
Set Bot Signal Thresholds to 5 to Enable Trading
Removes filters by setting very low thresholds
"""

import sqlite3
import json
from datetime import datetime

def set_low_thresholds():
    """Set signal thresholds to 5 for all enabled bots"""

    # Connect to database
    db_path = r'Zwesta Flutter App\zwesta_trading.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🎯 SETTING BOT SIGNAL THRESHOLDS TO 5")
    print("="*50)

    # Show current bot thresholds
    print("\n📊 CURRENT BOT THRESHOLDS:")
    cursor.execute('SELECT bot_id, name, status, enabled FROM user_bots WHERE enabled = 1')
    bots = cursor.fetchall()

    for bot in bots:
        bot_id, name, status, enabled = bot
        print(f"   🤖 {name} ({bot_id[:20]}...): {status}")

    # Update runtime_state for all enabled bots
    cursor.execute('SELECT bot_id, name, runtime_state FROM user_bots WHERE enabled = 1')
    all_bots = cursor.fetchall()

    updated_count = 0
    for bot in all_bots:
        bot_id, name, runtime_state_json = bot
        if runtime_state_json:
            try:
                runtime_state = json.loads(runtime_state_json)
                runtime_state['signalThreshold'] = 5
                runtime_state['effectiveSignalThreshold'] = 5
                # Remove adaptive offset to prevent it from increasing threshold
                runtime_state['adaptiveSignalThresholdOffset'] = 0
                cursor.execute('UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?', (json.dumps(runtime_state), bot_id))
                updated_count += 1
            except json.JSONDecodeError:
                print(f"   ⚠️  Could not parse runtime_state for {name}")
        else:
            # Create runtime_state if missing
            runtime_state = {
                'signalThreshold': 5,
                'effectiveSignalThreshold': 5,
                'adaptiveSignalThresholdOffset': 0
            }
            cursor.execute('UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?', (json.dumps(runtime_state), bot_id))
            updated_count += 1

    conn.commit()

    # Verify changes
    print(f"\n✅ Updated {updated_count} active bots runtime state")
    print("\n📊 UPDATED THRESHOLDS:")
    cursor.execute('SELECT bot_id, name, runtime_state FROM user_bots WHERE enabled = 1')
    updated_bots = cursor.fetchall()

    for bot in updated_bots:
        bot_id, name, runtime_state_json = bot
        if runtime_state_json:
            try:
                runtime_state = json.loads(runtime_state_json)
                threshold = runtime_state.get('signalThreshold', 'N/A')
                print(f"   🤖 {name}: {threshold}/100 threshold")
            except:
                print(f"   🤖 {name}: Error parsing")
        else:
            print(f"   🤖 {name}: No runtime_state")

    conn.close()

    print("\n🎉 Bots should now trade with any signal strength >= 5!")
    print("   Filters removed - thresholds set to minimum.")
    print("   Monitor your backend logs to see trading activity.")

if __name__ == '__main__':
    set_low_thresholds()