#!/usr/bin/env python3
"""Check and fix existing MT5 credentials"""
import requests
import json

API_BASE = 'http://localhost:9000'
EMAIL = 'zwexman@gmail.com'
PASSWORD = 'Zwesta1985'

# Login
response = requests.post(
    f'{API_BASE}/api/user/login',
    json={'email': EMAIL, 'password': PASSWORD},
    timeout=10
)

token = response.json().get('session_token')

# Get all credentials
response = requests.get(
    f'{API_BASE}/api/broker/credentials',
    headers={'X-Session-Token': token},
    timeout=10
)

creds = response.json().get('credentials', [])

print("=" * 80)
print("ALL YOUR BROKER CREDENTIALS:")
print("=" * 80)
for i, c in enumerate(creds, 1):
    print(f"\n{i}. Credential ID: {c.get('credential_id')}")
    print(f"   Broker: {c.get('broker_name') or 'Not set'}")
    print(f"   Account: {c.get('account_number')}")
    print(f"   Server: {c.get('server') or 'Not set'}")
    print(f"   Type: {c.get('account_type') or ('LIVE' if c.get('is_live') else 'DEMO')}")
    print(f"   Active: {c.get('is_active', 'Unknown')}")

print("\n" + "=" * 80)
print("\nIf you see your Exness MT5 account above but broker_name is missing,")
print("we can fix it. Otherwise, add credentials via the app.")
print("=" * 80)
