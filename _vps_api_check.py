"""
Connect to VPS API and diagnose bot state.
Uses a token from the VPS DB snapshot.
"""
import requests, json

VPS = 'http://148.113.5.39:9000'
TOKEN = 'd2e93e00da2e04cdd815475b17a61cc6cbcdf02a75cc2a5ef9c3e9c472da3cc5'
HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}

def get(path):
    try:
        r = requests.get(f'{VPS}{path}', headers=HEADERS, timeout=20)
        return r.status_code, r.json() if r.content else {}
    except Exception as e:
        return 0, str(e)

# Try to get bots
endpoints = ['/api/user/bots', '/api/bots', '/api/bot/list', '/api/status']
for ep in endpoints:
    code, data = get(ep)
    print(f"{ep} -> {code}")
    if code == 200:
        print(json.dumps(data, indent=2)[:2000])
        break
    elif code != 0:
        print(f"  Response: {str(data)[:200]}")
    print()
