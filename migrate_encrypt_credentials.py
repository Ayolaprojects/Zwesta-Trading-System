"""One-shot migration: encrypt every plaintext api_key + password row in
broker_credentials. Idempotent — already-encrypted rows are skipped via the
marker prefix.

Usage:
    python migrate_encrypt_credentials.py
"""
import os, sys, sqlite3

# Ensure we use the same key resolution as the backend
sys.path.insert(0, r'C:\backend')
from credential_crypto import encrypt_secret  # type: ignore

DB = os.environ.get('ZWESTA_DB_PATH') or r'C:\backend\zwesta_trading.db'

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT credential_id, api_key, password FROM broker_credentials')
rows = cur.fetchall()

updated = 0
skipped = 0
for r in rows:
    cid = r['credential_id']
    api_key_v = r['api_key']
    password_v = r['password']
    new_api_key = encrypt_secret(api_key_v) if api_key_v else api_key_v
    new_password = encrypt_secret(password_v) if password_v else password_v
    if new_api_key == api_key_v and new_password == password_v:
        skipped += 1
        continue
    cur.execute(
        'UPDATE broker_credentials SET api_key = ?, password = ? WHERE credential_id = ?',
        (new_api_key, new_password, cid),
    )
    updated += 1

conn.commit()
conn.close()
print(f'Encrypted {updated} credential row(s); {skipped} already-encrypted/empty row(s) skipped.')
