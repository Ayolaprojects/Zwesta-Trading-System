#!/usr/bin/env python3
"""Diagnostic script to inspect bot summary data vs. trades table."""
import json
import os
import sys

import requests

VPS = os.environ.get('VPS_URL', 'http://localhost:9000')

# Credentials — override via env vars
EMAIL = os.environ.get('VPS_EMAIL', 'trader2@example.com')
PASSWORD = os.environ.get('VPS_PASSWORD', 'password123')

def login():
    r = requests.post(f'{VPS}/api/user/login', json={'email': EMAIL, 'password': PASSWORD}, timeout=15)
    d = r.json()
    token = d.get('session_token', '')
    uid = d.get('user_id', '')
    print(f"Login: {r.status_code} | user_id={uid} | token={token[:16]}...")
    return token, uid

def call_summary(token, mode='ALL'):
    url = f'{VPS}/api/bot/summary?mode={mode}&include_broker_snapshots=true'
    headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, timeout=30)
    print(f"\nGET {url}")
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error: {r.text[:500]}")
        return None
    data = r.json()
    print(f"success: {data.get('success')}")
    print(f"effectiveUserId: {data.get('effectiveUserId')}")
    print(f"databaseBackend: {data.get('databaseBackend')}")
    print(f"databaseTarget: {data.get('databaseTarget')}")
    bots = data.get('bots', [])
    print(f"bot_count: {len(bots)}")
    for b in bots:
        print(json.dumps({
            'botId': b.get('botId'),
            'enabled': b.get('enabled'),
            'status': b.get('status'),
            'mode': b.get('mode'),
            'strategy': b.get('strategy'),
            'symbol': b.get('symbol'),
            'profit': b.get('profit'),
            'totalProfit': b.get('totalProfit'),
            'allTimeProfit': b.get('allTimeProfit'),
            'totalTrades': b.get('totalTrades'),
            'winRate': b.get('winRate'),
            'openPositionsCount': b.get('openPositionsCount'),
            'openPositionsPreview': len(b.get('openPositionsPreview', [])),
            'floatingProfit': b.get('floatingProfit'),
            'currentProfit': b.get('currentProfit'),
            'sessionProfit': b.get('sessionProfit'),
            'dailyProfit': b.get('dailyProfit'),
            'brokerName': b.get('brokerName'),
            'accountBalance': b.get('accountBalance'),
        }, indent=2))
    return bots

def call_status(token):
    url = f'{VPS}/api/bot/status'
    headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}
    r = requests.get(url, headers=headers, timeout=15)
    print(f"\nGET {url}")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        bots = data.get('bots', [])
        print(f"bot_status_count: {len(bots)}")
        for b in bots[:10]:
            print(f"  botId={b.get('botId')} enabled={b.get('enabled')} status={b.get('status')} mode={b.get('mode')} totalProfit={b.get('totalProfit')} totalTrades={b.get('totalTrades')} open_positions={len(b.get('open_positions', {}))}")
    return r

def direct_db_query(token, uid):
    """Try to use the backend's own DB access via an endpoint that returns trade data."""
    # Check if there's a trades endpoint
    endpoints = ['/api/trades', '/api/trades/list', '/api/bot/trades']
    headers = {'X-Session-Token': token, 'Content-Type': 'application/json'}
    for ep in endpoints:
        try:
            r = requests.get(f'{VPS}{ep}', headers=headers, timeout=10)
            if r.status_code == 200:
                print(f"\n{ep}: {r.status_code}")
                print(json.dumps(r.json(), indent=2)[:1000])
        except Exception:
            pass

if __name__ == '__main__':
    print("=" * 70)
    print("BOT SUMMARY DIAGNOSTIC")
    print(f"VPS URL: {VPS}")
    print(f"Email: {EMAIL}")
    print("=" * 70)

    token, uid = login()

    if not token:
        print("FAILED to get session token. Check credentials.")
        sys.exit(1)

    call_summary(token, mode='ALL')
    call_status(token)
    direct_db_query(token, uid)

    print("\n" + "=" * 70)
    print("If bots appear in /api/bot/status but show zero trades/profit in")
    print("/api/bot/summary, the issue is in the summary endpoint's trade-stats")
    print("merge logic (now fixed — see bot_summary runtime bot section)")
    print("=" * 70)
