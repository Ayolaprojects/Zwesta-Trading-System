#!/usr/bin/env python3
"""
Test existing Binance bots to verify they're executing trades.
Uses admin credentials to check bot status and trading activity.
"""
import requests
import json
import time

BASE_URL = "http://localhost:9000"

def test_existing_binance_bots():
    """Check existing Binance bots for trade execution."""
    
    print("=" * 70)
    print("CHECKING EXISTING BINANCE BOTS FOR TRADE EXECUTION")
    print("=" * 70)
    
    # Login as admin
    print("\n1. Login as admin")
    login_resp = requests.post(
        f"{BASE_URL}/api/user/login",
        json={"email": "admin@zwesta.com", "password": "admin"},
        timeout=10
    )
    print(f"   Login: {login_resp.status_code}")
    
    if login_resp.status_code != 200:
        print(f"   ❌ Failed: {login_resp.json()}")
        return False
    
    user_data = login_resp.json()
    token = user_data.get("token")
    print(f"   ✅ Logged in")
    
    # Get all bots
    print("\n2. Fetching all bots")
    bots_resp = requests.get(
        f"{BASE_URL}/api/bots",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    print(f"   Response: {bots_resp.status_code}")
    
    if bots_resp.status_code != 200:
        print(f"   ❌ Failed: {bots_resp.json()}")
        return False
    
    bots_data = bots_resp.json()
    bots = bots_data.get("bots", [])
    print(f"   Found {len(bots)} bots")
    
    # Analyze each bot
    print("\n3. Bot Trading Activity Analysis")
    print("-" * 70)
    
    binance_bots = [b for b in bots if b.get("broker") == "binance"]
    print(f"\n   Binance bots: {len(binance_bots)}")
    
    for bot in binance_bots:
        bot_id = bot.get("bot_id")
        bot_name = bot.get("name")
        status = bot.get("status")
        
        print(f"\n   Bot: {bot_name} ({bot_id})")
        print(f"   Status: {status}")
        print(f"   Symbols: {bot.get('symbols', [])}")
        print(f"   P&L: {bot.get('profit', 0):.4f} {bot.get('currency', 'USDT')}")
        
        # Get detailed bot stats
        stats_resp = requests.get(
            f"{BASE_URL}/api/bot/{bot_id}/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            print(f"   Total Trades: {stats.get('total_trades', 0)}")
            print(f"   Open Positions: {stats.get('open_positions', 0)}")
            print(f"   Closed Trades: {stats.get('closed_trades', 0)}")
            print(f"   Win Rate: {stats.get('win_rate', 0):.1%}")
            print(f"   Last Trade: {stats.get('last_trade_time', 'N/A')}")
        
        # Get positions
        positions_resp = requests.get(
            f"{BASE_URL}/api/bot/{bot_id}/positions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if positions_resp.status_code == 200:
            positions = positions_resp.json().get("positions", [])
            print(f"\n   Open Positions ({len(positions)}):")
            for pos in positions[:3]:  # Show first 3
                print(f"     - {pos.get('symbol')}: {pos.get('direction')} @ {pos.get('entry_price')}")
                print(f"       P&L: {pos.get('pnl', 0):.4f}")
    
    # Exness bots
    exness_bots = [b for b in bots if b.get("broker") == "exness"]
    print(f"\n\n   Exness bots: {len(exness_bots)}")
    
    for bot in exness_bots[:2]:  # Check first 2 Exness bots
        bot_id = bot.get("bot_id")
        bot_name = bot.get("name")
        status = bot.get("status")
        
        print(f"\n   Bot: {bot_name} ({bot_id})")
        print(f"   Status: {status}")
        print(f"   Symbols: {bot.get('symbols', [])}")
        print(f"   P&L: {bot.get('profit', 0):.4f} {bot.get('currency', 'USD')}")
    
    print("\n" + "=" * 70)
    print("✅ BOT ANALYSIS COMPLETE")
    print("=" * 70)
    return True

if __name__ == "__main__":
    try:
        success = test_existing_binance_bots()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
