#!/usr/bin/env python3
"""Get detailed bot info including trading status."""

import requests
import sqlite3
import json

BASE = 'http://148.113.5.39:9000'

def get_session_token():
    try:
        lr = requests.post(f'{BASE}/api/user/login', 
                          json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, 
                          timeout=10)
        return lr.json().get('session_token', '')
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return None

def get_detailed_bot_info(token):
    """Get detailed config for each bot."""
    try:
        headers = {'X-Session-Token': token}
        r = requests.get(f'{BASE}/api/bot/status', headers=headers, timeout=10)
        bots = r.json().get('bots', [])
        
        print("\n" + "=" * 80)
        print("DETAILED BOT INFO")
        print("=" * 80)
        
        for b in bots:
            bid = b.get('botId')
            print(f"\n📊 {bid}")
            print(f"   Status: {b.get('status')}")
            print(f"   Enabled: {b.get('enabled')}")
            print(f"   Trading Amount: {b.get('tradeAmount')}")
            print(f"   Daily Profit: {b.get('dailyProfit')}")
            print(f"   Total Profit: {b.get('totalProfit')}")
            print(f"   Account Balance: {b.get('accountBalance')}")
            print(f"   Paused: {b.get('paused')}")
            print(f"   Paused Until: {b.get('pausedUntil')}")
            print(f"   Trading Disabled: {b.get('tradingDisabled')}")
            
            # Get detailed config
            try:
                r2 = requests.get(f'{BASE}/api/bot/config/{requests.utils.quote(bid)}', 
                                 headers=headers, timeout=10)
                cfg = r2.json().get('config', {})
                print(f"   Broker: {cfg.get('brokerName')}")
                print(f"   Symbols: {len(cfg.get('symbols', []))} symbols")
                print(f"   Management Mode: {cfg.get('managementMode')}")
                print(f"   Signal Threshold: {cfg.get('signalThreshold')}")
            except:
                pass
            
            # Check recent trades in database
            try:
                db = r'C:\backend\zwesta_trading.db'
                c = sqlite3.connect(db)
                cur = c.cursor()
                
                # Count recent trades (last 24h)
                cur.execute("""
                    SELECT COUNT(*) FROM trades 
                    WHERE bot_id = ? AND created_at > datetime('now', '-1 day')
                """, (bid,))
                count = cur.fetchone()[0]
                
                # Get last trade
                cur.execute("""
                    SELECT closed_at, profit, status FROM trades 
                    WHERE bot_id = ? ORDER BY closed_at DESC LIMIT 1
                """, (bid,))
                last = cur.fetchone()
                
                print(f"   Trades (24h): {count}")
                if last:
                    print(f"   Last Trade: {last[0]} | Profit: {last[1]} | Status: {last[2]}")
                else:
                    print(f"   Last Trade: NONE")
                
                c.close()
            except Exception as e:
                print(f"   DB Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    token = get_session_token()
    if token:
        get_detailed_bot_info(token)
