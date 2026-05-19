"""Minimal patch test - just tradeAmount to isolate the timeout issue"""
import requests, json

BASE = 'http://148.113.5.39:9000'
lr = requests.post(f'{BASE}/api/user/login', json={'email':'zwexman@gmail.com','password':'Zwesta1985'}, timeout=10)
d = lr.json()
token = d.get('session_token','')
SH = {'X-Session-Token': token}

# Check bot state first
r = requests.get(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, timeout=10)
cfg = r.json().get('config', {})
print(f"enabled: {cfg.get('enabled')} tradeAmount: {cfg.get('tradeAmount')}")
print(f"All keys: {sorted(cfg.keys())}")

# Minimal patch: ONLY change tradeAmount (no scanner, no symbols, no retrace reset)
patch = {
    'credentialId': cfg.get('credentialId'),
    'tradeAmount': 20.0,
    # Keep everything else as-is by NOT passing other fields
}

print(f'\nSending minimal PUT (only tradeAmount: 20)...')
try:
    r2 = requests.put(f'{BASE}/api/bot/config/AZE%20BOT', headers=SH, json=patch, timeout=30)
    print(f'Result: {r2.status_code} {r2.text[:400]}')
except Exception as e:
    print(f'Error: {e}')
