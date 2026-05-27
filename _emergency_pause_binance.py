#!/usr/bin/env python3
"""
EMERGENCY FIX - Force pause Binance bot and verify all settings
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\backend\zwesta_trading.db'

def emergency_pause_binance_bot():
    """Force pause Binance bot with minimal config"""
    
    print("=" * 80)
    print("🚨 EMERGENCY FIX - PAUSING BINANCE BOT")
    print("=" * 80)
    print()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get current state
    cur.execute("SELECT bot_id, name, runtime_state FROM user_bots WHERE bot_id = 'bot_1779229018996'")
    row = cur.fetchone()
    
    if not row:
        print("❌ Bot not found!")
        conn.close()
        return
    
    bot_id, name, runtime_state = row
    
    print(f"📝 Bot: {bot_id} ({name})")
    print()
    
    # Create minimal paused config
    minimal_config = {
        "symbols": [],  # EMPTY - no trading
        "signalThreshold": 70,
        "maxOpenPositions": 2,
        "maxPositionsPerSymbol": 1,
        "managementProfile": "balanced",
        "pauseReason": "EMERGENCY PAUSE - Crypto unprofitable (Binance analysis shows losses)",
        "pausedAt": datetime.now().isoformat(),
        "pausedBy": "emergency_fix_script"
    }
    
    print("🔧 Applying MINIMAL PAUSED CONFIG:")
    print(f"   symbols: {minimal_config['symbols']}")
    print(f"   Reason: {minimal_config['pauseReason']}")
    print()
    
    # UPDATE with minimal config
    cur.execute("""
        UPDATE user_bots 
        SET runtime_state = ? 
        WHERE bot_id = ?
    """, (json.dumps(minimal_config), bot_id))
    
    conn.commit()
    
    print("✅ Database updated")
    print()
    
    # Verify
    cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (bot_id,))
    new_state = json.loads(cur.fetchone()[0])
    
    print("🔍 VERIFICATION:")
    print(f"   symbols: {new_state.get('symbols')}")
    print(f"   pauseReason: {new_state.get('pauseReason')}")
    print(f"   pausedAt: {new_state.get('pausedAt')}")
    print()
    
    if new_state.get('symbols') == []:
        print("✅ BINANCE BOT SUCCESSFULLY PAUSED")
    else:
        print(f"❌ VERIFICATION FAILED - symbols still: {new_state.get('symbols')}")
    
    conn.close()

if __name__ == "__main__":
    emergency_pause_binance_bot()
