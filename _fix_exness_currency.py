"""
Run this script DIRECTLY ON THE VPS (via RDP).
Fixes the Exness credential account_currency from 'USDT' → 'ZAR'.

Usage:  python C:\zwesta-trader\_fix_exness_currency.py
"""

import sqlite3, os, glob, sys

CREDENTIAL_ID = '9f14c8b4-0071-4222-81a2-5c99e841b9e0'
CORRECT_CURRENCY = 'ZAR'

candidates = [
    r'C:\backend\zwesta_trading.db',
    r'C:\zwesta_trading.db',
]
for pattern in [r'C:\*\*.db', '/home/*/backend/*.db']:
    candidates += glob.glob(pattern)

db_path = None
for c in candidates:
    if os.path.exists(c):
        db_path = c
        break

if not db_path:
    print("ERROR: Could not find zwesta_trading.db")
    sys.exit(1)

print(f"Using DB: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

row = conn.execute(
    'SELECT credential_id, account_number, account_currency FROM broker_credentials WHERE credential_id = ?',
    (CREDENTIAL_ID,)
).fetchone()

if not row:
    print(f"ERROR: Credential {CREDENTIAL_ID} not found in DB")
    conn.close()
    sys.exit(1)

print(f"Found credential: account={row['account_number']}  current currency={row['account_currency']}")

if row['account_currency'] == CORRECT_CURRENCY:
    print(f"Currency is already {CORRECT_CURRENCY} — nothing to do.")
    conn.close()
    sys.exit(0)

conn.execute(
    'UPDATE broker_credentials SET account_currency = ? WHERE credential_id = ?',
    (CORRECT_CURRENCY, CREDENTIAL_ID)
)
conn.commit()

verify = conn.execute(
    'SELECT account_currency FROM broker_credentials WHERE credential_id = ?',
    (CREDENTIAL_ID,)
).fetchone()
print(f"✅ Currency updated: {row['account_currency']} → {verify['account_currency']}")
conn.close()
