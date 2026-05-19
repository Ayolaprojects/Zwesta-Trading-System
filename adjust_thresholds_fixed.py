#!/usr/bin/env python3
"""
Adjust Bot Signal Thresholds to Enable Trading
Lower signal thresholds to allow trading with current signal strengths
"""

import sqlite3
import json
import os

def adjust_signal_thresholds():
    """Lower signal thresholds to enable trading with current market conditions"""
    db_path = r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    print("🎯 ADJUSTING BOT SIGNAL THRESHOLDS")
    print("=" * 50)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get current bot thresholds
        cursor.execute('''
            SELECT bot_id, name, runtime_state
            FROM user_bots
            WHERE enabled = 1 AND status = 'active'
        ''')

        bots = cursor.fetchall()
        print("\n📊 CURRENT BOT THRESHOLDS:")
        for bot in bots:
            runtime_state = json.loads(bot['runtime_state'] or '{}')
            threshold = runtime_state.get('signalThreshold', 'N/A')
            print(f"   🤖 {bot['name'][:30]}...: {threshold}/100 threshold")

        # Update thresholds to 10/100 (allows trading with current 10/100 signals)
        print("\n🔧 ADJUSTING THRESHOLDS TO 10/100...")

        updated_count = 0
        for bot in bots:
            runtime_state = json.loads(bot['runtime_state'] or '{}')
            runtime_state['signalThreshold'] = 10
            runtime_state['effectiveSignalThreshold'] = 10

            cursor.execute('''
                UPDATE user_bots
                SET runtime_state = ?
                WHERE bot_id = ?
            ''', (json.dumps(runtime_state), bot['bot_id']))

            updated_count += 1

        conn.commit()
        conn.close()

        print(f"✅ Updated {updated_count} bots to signal threshold 10/100")
        print("\n🔄 RESTART the backend server for changes to take effect!")
        print("   The bots will now trade when signals reach 10/100 strength")

    except Exception as e:
        print(f"❌ Error adjusting thresholds: {e}")

if __name__ == "__main__":
    adjust_signal_thresholds()