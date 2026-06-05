#!/usr/bin/env python3
"""
Copy bot configuration from working bot to new Max bot
Source: bot_1779229018996 (Scalping, Binance - working)
Target: bot_1780655548458 (Max sint trading - new)
"""

import json
import shutil
from datetime import datetime

CONFIG_FILE = 'bot_status.json'

def load_config():
    """Load bot status config"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {CONFIG_FILE}")
        return None

def save_config(data):
    """Save bot status config"""
    # Backup first
    backup = f"{CONFIG_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(CONFIG_FILE, backup)
    print(f"💾 Backed up to: {backup}")
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved to: {CONFIG_FILE}")

def copy_bot_config():
    """Copy working bot config to new bot"""
    
    data = load_config()
    if not data:
        return False
    
    bots = data.get('bots', [])
    
    # Find source and target bots
    source_bot = None
    target_idx = None
    
    for i, bot in enumerate(bots):
        bot_id = bot.get('botId', '')
        if bot_id == 'bot_1779229018996':
            source_bot = bot.copy()
            print(f"✅ Found source bot: {bot_id}")
            print(f"   Strategy: {bot.get('strategy')}")
            print(f"   Broker: {bot.get('broker_type')}")
            print(f"   Symbols: {bot.get('symbols')}")
            print(f"   Management Profile: {bot.get('managementProfile')}")
        elif bot_id == 'bot_1780655548458':
            target_idx = i
            print(f"✅ Found target bot: {bot_id}")
            print(f"   Current Strategy: {bot.get('strategy')}")
    
    if not source_bot:
        print("❌ Could not find source bot (bot_1779229018996)")
        return False
    
    if target_idx is None:
        print("❌ Could not find target bot (bot_1780655548458)")
        return False
    
    # Copy key trading parameters from source to target
    print("\n📋 Copying configuration...")
    
    target_bot = bots[target_idx]
    
    # Copy essential trading params
    params_to_copy = [
        'strategy',
        'symbols',
        'managementProfile',
        'managementMode',
        'managementState',
        'signalThreshold',
        'maxOpenPositions',
        'maxPositionsPerSymbol',
        'displayCurrency',
    ]
    
    for param in params_to_copy:
        if param in source_bot:
            old_val = target_bot.get(param)
            new_val = source_bot[param]
            target_bot[param] = new_val
            if old_val != new_val:
                print(f"  {param}: {old_val} → {new_val}")
    
    # Update timestamps
    target_bot['lastModified'] = datetime.now().isoformat()
    
    # Save updated config
    print("\n💾 Saving updated configuration...")
    save_config(data)
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURATION COPIED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nTarget bot (1780655548458) now configured like source (1779229018996)")
    print(f"Strategy: {target_bot['strategy']}")
    print(f"Symbols: {target_bot['symbols']}")
    print(f"Management Profile: {target_bot.get('managementProfile')}")
    print(f"\nBot will restart and begin trading with these settings.\n")
    
    return True

if __name__ == '__main__':
    success = copy_bot_config()
    exit(0 if success else 1)
