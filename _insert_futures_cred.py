"""
Direct DB insert of Binance Futures demo credential.
Bypasses the API (which tries to connect to Binance on save → times out).
"""
import sys, sqlite3, json, uuid
from datetime import datetime
sys.path.insert(0, r'C:\backend')
from credential_crypto import decrypt_secret, encrypt_secret

db = r'C:\backend\zwesta_trading.db'
uid = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
SPOT_CRED_ID = 'e568ec38-cfc7-4b05-8033-b56ecdf304e4'

# ── Read + decrypt existing spot key ─────────────────────────────────────────
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()
row = c.execute("SELECT api_key, password FROM broker_credentials WHERE credential_id=?", (SPOT_CRED_ID,)).fetchone()
api_key_enc = row['api_key']
api_sec_enc = row['password']

api_key = decrypt_secret(api_key_enc) if api_key_enc and api_key_enc.startswith('enc:') else api_key_enc
api_sec = decrypt_secret(api_sec_enc) if api_sec_enc and api_sec_enc.startswith('enc:') else api_sec_enc
print(f"Decrypted key: {api_key[:10]}... secret: {api_sec[:6]}...")

# ── Re-encrypt for storage ────────────────────────────────────────────────────
enc_key = encrypt_secret(api_key)
enc_sec = encrypt_secret(api_sec)
print(f"Re-encrypted key: {enc_key[:20]}...")

# ── Insert futures demo credential ────────────────────────────────────────────
new_id = str(uuid.uuid4())
now = datetime.utcnow().isoformat()

c.execute('''
    INSERT INTO broker_credentials
      (credential_id, user_id, broker_name, account_number, api_key, password, server, label,
       is_live, is_active, created_at, updated_at)
    VALUES (?, ?, 'Binance', 'BINANCE-FUTURES-DEMO', ?, ?, 'futures', 'Binance Futures Demo',
            0, 1, ?, ?)
''', (new_id, uid, enc_key, enc_sec, now, now))

conn.commit()
print(f"\nInserted Binance Futures DEMO credential: {new_id}")

# ── Verify ────────────────────────────────────────────────────────────────────
rows = c.execute("SELECT credential_id, label, server, is_live FROM broker_credentials WHERE user_id=?", (uid,)).fetchall()
print("\nAll credentials now:")
for r in rows:
    print(f"  {r['credential_id']} | {r['label']} | server={r['server']} | is_live={r['is_live']}")

conn.close()
print(f"\nFutures credential ID to use: {new_id}")
