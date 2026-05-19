#!/usr/bin/env python3
"""
Adjust Bot Signal Thresholds to Enable Trading
Temporarily lowers thresholds so bots can trade with current signal levels
"""

import sqlite3
from datetime import datetime

def adjust_signal_thresholds():
    """Lower signal thresholds to enable trading with current market conditions"""

    # Connect to database
    db_path = r'Zwesta Flutter App\zwesta_trading.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🎯 ADJUSTING BOT SIGNAL THRESHOLDS")
    print("="*50)

    # Show current bot thresholds
    print("\n📊 CURRENT BOT THRESHOLDS:")
    cursor.execute('SELECT bot_id, name, strategy, status, enabled FROM user_bots WHERE enabled = 1')
    bots = cursor.fetchall()

    for bot in bots:
        bot_id, name, strategy, status, enabled = bot
        print(f"   🤖 {name} ({bot_id[:20]}...): {status}")

    # Adjust thresholds to 15/100 (allows trading with current 10/100 signals)
    print("\n🔧 ADJUSTING THRESHOLDS TO 15/100...")
    cursor.execute('UPDATE user_bots SET signal_threshold = 15 WHERE enabled = 1')
    conn.commit()

    # Verify changes
    print("\n✅ THRESHOLDS UPDATED:")
    cursor.execute('SELECT bot_id, name, signal_threshold FROM user_bots WHERE enabled = 1')
    updated_bots = cursor.fetchall()

    for bot in updated_bots:
        bot_id, name, threshold = bot
        print(f"   🤖 {name}: {threshold}/100 threshold")

    conn.close()

    print("\n🎉 Bots should now start trading within the next signal check cycle!")
    print("   Monitor your backend logs to see trading activity.")
    print("\n💡 You can adjust thresholds back up later when market conditions improve.")
    print("   Recommended: 35-50/100 for normal trading, 60+/100 for conservative.")

if __name__ == '__main__':
    adjust_signal_thresholds()