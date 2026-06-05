#!/usr/bin/env python3
"""
Map new 'Max sint trading' bot to use Zwesta bot's working configuration
"""

import sqlite3
import json
import sys
from datetime import datetime

DB_PATH = r'c:\zwesta-trader\zwesta.db'

def get_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_zwesta_bot():
    """Find the working Zwesta bot"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Search for bot with 'zwesta' or 'Zwesta' in name or ID
    cursor.execute("""
        SELECT bot_id, name, strategy, enabled 
        FROM user_bots 
        WHERE LOWER(name) LIKE '%zwesta%' 
           OR LOWER(bot_id) LIKE '%zwesta%'
        LIMIT 1
    """)
    
    zwesta_bot = cursor.fetchone()
    conn.close()
    return zwesta_bot

def find_max_bot():
    """Find the new Max bot"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Search for bot with 'max' in name
    cursor.execute("""
        SELECT bot_id, name, enabled
        FROM user_bots 
        WHERE LOWER(name) LIKE '%max%'
           OR LOWER(name) LIKE '%sint%'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    max_bot = cursor.fetchone()
    conn.close()
    return max_bot

def get_bot_config_from_runtime_state(bot_id):
    """Load bot config from runtime_state JSON file"""
    try:
        import glob
        pattern = f"*{bot_id}*runtime*.json"
        files = glob.glob(pattern)
        if files:
            with open(files[0], 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️  Could not load runtime state JSON: {e}")
    return None

def copy_bot_config(source_bot_id, target_bot_id):
    """Copy strategy config from source to target bot"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get source bot's full config
    cursor.execute("""
        SELECT * FROM user_bots WHERE bot_id = ?
    """, (source_bot_id,))
    
    source_row = cursor.fetchone()
    if not source_row:
        print(f"❌ Source bot {source_bot_id} not found")
        conn.close()
        return False
    
    print(f"📋 Found source bot: {source_row['name']} ({source_bot_id})")
    print(f"   Strategy: {source_row['strategy']}")
    print(f"   Symbols: {source_row['symbols']}")
    
    # Copy key fields to target bot
    try:
        cursor.execute("""
            UPDATE user_bots 
            SET 
                strategy = ?,
                symbols = ?,
                updated_at = ?
            WHERE bot_id = ?
        """, (
            source_row['strategy'],
            source_row['symbols'],
            datetime.now().isoformat(),
            target_bot_id
        ))
        
        conn.commit()
        print(f"✅ Copied strategy config to {target_bot_id}")
        
        # Now copy runtime state if available
        cursor.execute("""
            SELECT bot_id FROM bot_runtime_state WHERE bot_id = ?
        """, (source_bot_id,))
        
        runtime_state = cursor.fetchone()
        if runtime_state:
            # Get full runtime state
            cursor.execute("""
                SELECT config FROM bot_runtime_state WHERE bot_id = ?
            """, (source_bot_id,))
            
            config_row = cursor.fetchone()
            if config_row and config_row['config']:
                config_data = json.loads(config_row['config'])
                
                # Update key trading parameters
                config_data.update({
                    'botId': target_bot_id,
                    'strategy': source_row['strategy'],
                    'symbols': source_row['symbols'].split(',') if source_row['symbols'] else [],
                })
                
                # Insert or update runtime state for target
                cursor.execute("""
                    INSERT OR REPLACE INTO bot_runtime_state (bot_id, config, updated_at)
                    VALUES (?, ?, ?)
                """, (
                    target_bot_id,
                    json.dumps(config_data),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                print(f"✅ Copied runtime state config")
                print(f"   Strategy: {config_data.get('strategy', 'N/A')}")
                print(f"   Risk/Trade: {config_data.get('riskPerTrade', 'N/A')}")
                print(f"   Max Daily Loss: {config_data.get('maxDailyLoss', 'N/A')}")
                print(f"   Signal Threshold: {config_data.get('signalThreshold', 'N/A')}")
                print(f"   Profit Lock: {config_data.get('profitLock', 'N/A')}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error copying config: {e}")
        conn.close()
        return False

def main():
    print("=" * 60)
    print("MAP MAX BOT TO ZWESTA CONFIGURATION")
    print("=" * 60)
    
    # Find both bots
    print("\n🔍 Searching for bots...")
    zwesta_bot = find_zwesta_bot()
    max_bot = find_max_bot()
    
    if not zwesta_bot:
        print("❌ Could not find Zwesta bot")
        return False
    
    if not max_bot:
        print("❌ Could not find Max bot")
        return False
    
    print(f"\n📌 Source (Zwesta): {zwesta_bot['name']} - {zwesta_bot['bot_id']}")
    print(f"📌 Target (Max):    {max_bot['name']} - {max_bot['bot_id']}")
    
    # Copy configuration
    print("\n⏳ Copying configuration...")
    success = copy_bot_config(zwesta_bot['bot_id'], max_bot['bot_id'])
    
    if success:
        print("\n" + "=" * 60)
        print("✅ MAPPING COMPLETE")
        print("=" * 60)
        print(f"\n{max_bot['name']} ({max_bot['bot_id']}) is now configured like Zwesta bot")
        print("The bot should restart and begin trading with identical settings.\n")
        return True
    else:
        print("\n❌ Mapping failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
