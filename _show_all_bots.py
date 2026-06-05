#!/usr/bin/env python3
"""List all bots in the system."""

import requests
import json
import sqlite3

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

def list_all_bots(token):
    """List all bots from API."""
    try:
        headers = {'X-Session-Token': token}
        r = requests.get(f'{BASE}/api/bot/status', headers=headers, timeout=10)
        bots = r.json().get('bots', [])
        
        print(f"\n=== ALL BOTS FROM API ({len(bots)}) ===\n")
        
        for b in bots:
            bid = b.get('botId')
            name = b.get('name')
            broker = b.get('brokerName')
            status = b.get('status')
            enabled = b.get('enabled')
            print(f"{bid}")
            print(f"  name: {name}")
            print(f"  broker: {broker}")
            print(f"  status: {status}")
            print(f"  enabled: {enabled}")
            print()
    except Exception as e:
        print(f"❌ Error: {e}")

def list_db_bots():
    """List all bots from database."""
    try:
        db = r'C:\backend\zwesta_trading.db'
        c = sqlite3.connect(db)
        cur = c.cursor()
        
        cur.execute("SELECT bot_id, status, enabled FROM user_bots")
        rows = cur.fetchall()
        
        print(f"\n=== ALL BOTS FROM DATABASE ({len(rows)}) ===\n")
        for bot_id, status, enabled in rows:
            print(f"{bot_id} | status={status} | enabled={enabled}")
        
        c.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    token = get_session_token()
    if token:
        list_all_bots(token)
    list_db_bots()
