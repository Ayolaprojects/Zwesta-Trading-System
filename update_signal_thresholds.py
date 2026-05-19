#!/usr/bin/env python3
"""
Update Bot Signal Thresholds in Runtime State
Lowers thresholds so bots can trade with current signal levels
"""

import sqlite3
import json

def update_signal_thresholds():
    """Update signal thresholds in bot runtime state to enable trading"""

    conn = sqlite3.connect('Zwesta Flutter App/zwesta_trading.db')
    cursor = conn.cursor()

    print("🎯 UPDATING BOT SIGNAL THRESHOLDS IN RUNTIME STATE")
    print("="*55)

    # Get all enabled bots
    cursor.execute('SELECT bot_id, name, runtime_state FROM user_bots WHERE enabled = 1')
    bots = cursor.fetchall()

    print(f"\n📊 FOUND {len(bots)} ENABLED BOTS:")

    for bot_id, name, runtime_state in bots:
        print(f"\n🤖 {name}")
        print(f"   ID: {bot_id[:25]}...")

        if runtime_state:
            try:
                state = json.loads(runtime_state)

                # Show current threshold
                current_threshold = state.get('signalThreshold', 'Not set')
                print(f"   Current Threshold: {current_threshold}/100")

                # Update to 15 (allows trading with current 10/100 signals)
                state['signalThreshold'] = 15
                state['effectiveSignalThreshold'] = 15  # Also update effective

                # Save updated state
                updated_state = json.dumps(state)
                cursor.execute('UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?',
                             (updated_state, bot_id))

                print(f"   ✅ Updated Threshold: 15/100")

            except json.JSONDecodeError as e:
                print(f"   ❌ Error parsing runtime_state: {e}")
        else:
            print("   ⚠️ No runtime_state data")

    conn.commit()
    conn.close()

    print("\n🎉 SIGNAL THRESHOLDS UPDATED!")
    print("   Bots should start trading within the next signal check cycle.")
    print("   Monitor your backend logs for trading activity.")
    print("\n💡 Current market signals are ~10/100")
    print("   With 15/100 threshold, bots should now detect and trade signals.")
    print("\n🔄 You can adjust thresholds back up later when market conditions improve.")

if __name__ == '__main__':
    update_signal_thresholds()