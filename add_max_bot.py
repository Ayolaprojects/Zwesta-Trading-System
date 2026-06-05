#!/usr/bin/env python3
"""
Add new Max bot to bot_status.json with Zwesta (Scalping) configuration
"""

import json
from datetime import datetime
import shutil

CONFIG_FILE = 'bot_status.json'

def add_max_bot():
    """Add Max bot with Zwesta config"""
    
    # Load current config
    with open(CONFIG_FILE, 'r') as f:
        data = json.load(f)
    
    # Find the working Scalping bot
    source_bot = None
    for bot in data.get('bots', []):
        if bot.get('botId') == 'bot_1779229018996':
            source_bot = bot.copy()
            break
    
    if not source_bot:
        print("❌ Could not find source bot")
        return False
    
    print(f"✅ Source bot found: {source_bot['botId']}")
    print(f"   Strategy: {source_bot.get('strategy')}")
    
    # Create new bot entry for Max
    max_bot = source_bot.copy()
    max_bot['botId'] = 'bot_1780655548458'
    max_bot['lastModified'] = datetime.now().isoformat()
    max_bot['status'] = 'Active'
    max_bot['profit'] = 0
    max_bot['dailyProfit'] = 0
    max_bot['currentProfit'] = 0
    max_bot['totalProfit'] = 0
    max_bot['totalTrades'] = 0
    max_bot['winningTrades'] = 0
    max_bot['openPositions'] = []
    max_bot['currentRoi'] = 0
    max_bot['roi'] = 0
    
    # Backup first
    backup = f"{CONFIG_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(CONFIG_FILE, backup)
    print(f"💾 Backed up to: {backup}")
    
    # Add new bot
    data['bots'].append(max_bot)
    data['activeBots'] = len([b for b in data['bots'] if b.get('status') == 'Active'])
    
    # Save
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ MAX BOT ADDED WITH SCALPING CONFIGURATION")
    print("=" * 60)
    print(f"\nNew bot: bot_1780655548458")
    print(f"Strategy: {max_bot.get('strategy')}")
    print(f"Symbols: {max_bot.get('symbols')}")
    print(f"Management Profile: {max_bot.get('managementProfile')}")
    print(f"\nBot should now appear in your dashboard with working configuration.\n")
    
    return True

if __name__ == '__main__':
    try:
        success = add_max_bot()
        exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
