#!/usr/bin/env python3
"""Diagnose bot1780614250152 and Exness bot trading issues."""

import requests
import json
import sqlite3
from datetime import datetime

BASE = 'http://148.113.5.39:9000'

def get_session_token():
    """Login and get session token."""
    try:
        lr = requests.post(f'{BASE}/api/user/login', 
                          json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, 
                          timeout=10)
        return lr.json().get('session_token', '')
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return None

def check_bot_status(token, bot_id):
    """Get detailed bot status from API."""
    try:
        headers = {'X-Session-Token': token}
        r = requests.get(f'{BASE}/api/bot/status', headers=headers, timeout=10)
        bots = r.json().get('bots', [])
        
        for b in bots:
            if b.get('botId') == bot_id:
                print(f"\n=== BOT STATUS API: {bot_id} ===")
                for k in ['name','brokerName','enabled','status','tradeAmount','effectiveTradeAmount',
                         'managementMode','managementProfile','drawdownPauseUntil','totalProfit',
                         'dailyProfit','accountBalance','paused','tradingDisabled']:
                    v = b.get(k)
                    print(f"  {k}: {v}")
                return b
        
        print(f"\n❌ Bot {bot_id} not found in API status")
        return None
    except Exception as e:
        print(f"❌ Error checking bot status: {e}")
        return None

def check_bot_db(bot_id):
    """Check bot in local SQLite database."""
    try:
        db = r'C:\backend\zwesta_trading.db'
        c = sqlite3.connect(db)
        cur = c.cursor()
        
        cur.execute("SELECT bot_id, status, enabled, runtime_state, updated_at FROM user_bots WHERE bot_id = ?", (bot_id,))
        row = cur.fetchone()
        
        if row:
            bid, st, en, rs, up = row
            print(f"\n=== BOT DB: {bid} ===")
            print(f"  status: {st}")
            print(f"  enabled: {en}")
            print(f"  updated_at: {up}")
            
            if rs:
                try:
                    d = json.loads(rs)
                    print(f"  managementMode: {d.get('managementMode')}")
                    print(f"  signalThreshold: {d.get('signalThreshold')}")
                    print(f"  paused: {d.get('paused')}")
                    print(f"  tradingDisabled: {d.get('tradingDisabled')}")
                    print(f"  riskBreached: {d.get('riskBreached')}")
                    print(f"  dailyLossLimitHit: {d.get('dailyLossLimitHit')}")
                    print(f"  maxOpenReached: {d.get('maxOpenReached')}")
                    print(f"  emergencyStop: {d.get('emergencyStop')}")
                    print(f"  open_positions count: {len(d.get('open_positions', {}))}")
                except json.JSONDecodeError:
                    print(f"  ❌ Runtime state parse error")
        else:
            print(f"\n❌ Bot {bot_id} not found in database")
        
        c.close()
    except Exception as e:
        print(f"❌ Error checking database: {e}")

def check_exness_bots(token):
    """Check all Exness bots for trading issues."""
    try:
        headers = {'X-Session-Token': token}
        r = requests.get(f'{BASE}/api/bot/status', headers=headers, timeout=10)
        bots = r.json().get('bots', [])
        
        exness_bots = [b for b in bots if 'exness' in b.get('brokerName','').lower()]
        
        if not exness_bots:
            print("\n⚠️  No Exness bots found")
            return
        
        print(f"\n=== EXNESS BOTS ({len(exness_bots)}) ===")
        for b in exness_bots:
            bid = b.get('botId')
            print(f"\n  Bot: {bid}")
            print(f"    name: {b.get('name')}")
            print(f"    status: {b.get('status')}")
            print(f"    enabled: {b.get('enabled')}")
            print(f"    paused: {b.get('paused')}")
            print(f"    tradingDisabled: {b.get('tradingDisabled')}")
            print(f"    accountBalance: {b.get('accountBalance')}")
            print(f"    tradeAmount: {b.get('tradeAmount')}")
            print(f"    dailyProfit: {b.get('dailyProfit')}")
            
            # Check last trade time
            cur_session = sqlite3.connect(r'C:\backend\zwesta_trading.db').cursor()
            cur_session.execute(
                "SELECT MAX(closed_at) FROM trades WHERE bot_id = ? AND status = 'CLOSED'",
                (bid,)
            )
            last_closed = cur_session.fetchone()[0]
            if last_closed:
                print(f"    last_closed_trade: {last_closed}")
    except Exception as e:
        print(f"❌ Error checking Exness bots: {e}")

def main():
    print("=" * 60)
    print("BOT DIAGNOSTIC REPORT")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    token = get_session_token()
    if not token:
        print("Cannot proceed without valid session token")
        return
    
    # Check specific bot
    print("\n📋 CHECKING BOT bot1780614250152")
    bot_data = check_bot_status(token, 'bot1780614250152')
    check_bot_db('bot1780614250152')
    
    # Check Exness bots
    print("\n📋 CHECKING EXNESS BOTS")
    check_exness_bots(token)
    
    print("\n" + "=" * 60)
    print("TROUBLESHOOTING TIPS:")
    print("=" * 60)
    print("- If 'enabled' is False: Bot is disabled")
    print("- If 'paused' is True: Bot is paused (check pausedUntil)")
    print("- If 'tradingDisabled' is True: Trading is disabled")
    print("- If 'dailyLossLimitHit' is True: Hit daily loss limit")
    print("- If 'riskBreached' is True: Risk thresholds exceeded")
    print("- Flash trades: Check signal threshold and volatility settings")

if __name__ == '__main__':
    main()
