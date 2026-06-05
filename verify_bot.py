#!/usr/bin/env python3
"""
Verify new Binance bot is trading after creation
Run this after user creates a bot to confirm it's in the system
"""

import json
import requests
import sys
from datetime import datetime

BACKEND_URL = 'http://127.0.0.1:9000'  # Update to your VPS IP if remote
STATUS_FILE = 'bot_status.json'

def check_bot_in_status_file(bot_id):
    """Verify bot is in bot_status.json"""
    try:
        with open(STATUS_FILE, 'r') as f:
            data = json.load(f)
        
        for bot in data.get('bots', []):
            if bot.get('botId') == bot_id:
                return True, bot
        return False, None
    except Exception as e:
        print(f"❌ Error reading status file: {e}")
        return False, None

def check_bot_health(bot_id):
    """Check if bot is running on backend"""
    try:
        response = requests.get(f'{BACKEND_URL}/api/bot/status/{bot_id}', timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except Exception as e:
        print(f"⚠️  Backend check failed: {e}")
        return False, None

def start_trading(bot_id):
    """Force bot to start trading if not already"""
    try:
        response = requests.post(f'{BACKEND_URL}/api/bot/start/{bot_id}', timeout=5)
        if response.status_code in [200, 201]:
            return True
        return False
    except Exception as e:
        print(f"⚠️  Could not start bot: {e}")
        return False

def verify_new_bot(bot_id):
    """Full verification of new bot"""
    
    print(f"\n{'=' * 60}")
    print(f"VERIFYING NEW BOT: {bot_id}")
    print(f"{'=' * 60}\n")
    
    # Check 1: Is it in bot_status.json?
    print("✓ Checking status file...")
    in_status, bot_data = check_bot_in_status_file(bot_id)
    
    if in_status:
        print(f"✅ Bot found in bot_status.json")
        print(f"   Strategy: {bot_data.get('strategy')}")
        print(f"   Symbols: {bot_data.get('symbols')}")
        print(f"   Status: {bot_data.get('status')}")
        print(f"   Leverage: {bot_data.get('binanceFuturesBaseLeverage', 'N/A')}")
    else:
        print(f"❌ Bot NOT in bot_status.json - checking backend...")
        
        # Check 2: Is it on backend?
        in_backend, backend_data = check_bot_health(bot_id)
        if in_backend:
            print(f"✅ Bot found on backend (not yet synced to status file)")
            print(f"   Will sync on next refresh")
        else:
            print(f"❌ Bot NOT on backend either - creation may have failed")
            return False
    
    # Check 3: Ensure trading is enabled
    if in_status and bot_data:
        if bot_data.get('status') == 'Active' and bot_data.get('enabled'):
            print(f"\n✅ Bot is ACTIVE and ENABLED - should be trading now")
            return True
        else:
            print(f"\n⚠️  Bot exists but not trading yet")
            print(f"   Status: {bot_data.get('status')}")
            print(f"   Enabled: {bot_data.get('enabled')}")
            print(f"   Starting bot...")
            if start_trading(bot_id):
                print(f"✅ Started - bot should begin trading shortly")
                return True
            else:
                print(f"❌ Failed to start bot")
                return False
    
    return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python verify_bot.py <bot_id>")
        print("Example: python verify_bot.py bot_1780655548458")
        sys.exit(1)
    
    bot_id = sys.argv[1]
    success = verify_new_bot(bot_id)
    sys.exit(0 if success else 1)
