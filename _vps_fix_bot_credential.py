"""
_vps_fix_bot_credential.py
Run this ON THE VPS to fix bot_1780405618495 showing wrong (demo) account balance.

Problem: bot is marked LIVE and on account 295677214 but the bot_credentials
table links it to the DEMO credential (435760376), so the backend pulls the
wrong cached balance (R24k demo instead of your real R400+ live balance).

Fix: re-link bot_1780405618495 to the LIVE Exness 295677214 credential.
"""
import os, sys

DATABASE_BACKEND = os.getenv('DATABASE_BACKEND', 'sqlite').strip().lower()
DATABASE_URL = os.getenv('DATABASE_URL', '')

BOT_ID = 'bot_1780405618495'
LIVE_ACCOUNT = '295677214'
DEMO_ACCOUNT = '435760376'

if DATABASE_BACKEND == 'postgres' or DATABASE_URL.startswith('postgresql'):
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL or 'postgresql://zwesta_admin:Zwesta@Trading2026!@localhost:5432/zwesta_trading')
    cur = conn.cursor()
    placeholder = '%s'
else:
    import sqlite3
    DB_PATH = os.getenv('DATABASE_PATH', r'C:\backend\zwesta_trading.db')
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    placeholder = '?'

print(f"Connected (backend={DATABASE_BACKEND})")

# 1. Find the LIVE credential for Exness 295677214
cur.execute(
    f"SELECT credential_id, account_number, is_live, cached_balance, account_currency FROM broker_credentials WHERE account_number = {placeholder}",
    (LIVE_ACCOUNT,)
)
rows = cur.fetchall()
print("Live credential rows for", LIVE_ACCOUNT, ":", rows)
if not rows:
    print("ERROR: No credential found for account", LIVE_ACCOUNT)
    sys.exit(1)

live_cred_id = rows[0][0]
print(f"Will link {BOT_ID} -> credential {live_cred_id} (account {LIVE_ACCOUNT})")

# 2. Show current link
cur.execute(
    f"SELECT bc.bot_id, bc.credential_id, bcr.account_number, bcr.is_live FROM bot_credentials bc JOIN broker_credentials bcr ON bcr.credential_id = bc.credential_id WHERE bc.bot_id = {placeholder}",
    (BOT_ID,)
)
current = cur.fetchall()
print("Current bot_credentials link:", current)

# 3. Fix: update or insert the link to point to the live credential
if current:
    cur.execute(
        f"UPDATE bot_credentials SET credential_id = {placeholder} WHERE bot_id = {placeholder}",
        (live_cred_id, BOT_ID)
    )
    print(f"UPDATED bot_credentials: {BOT_ID} -> {live_cred_id}")
else:
    import datetime
    now = datetime.datetime.now().isoformat()
    cur.execute(
        f"INSERT INTO bot_credentials (bot_id, credential_id, user_id, created_at) SELECT {placeholder}, {placeholder}, user_id, {placeholder} FROM user_bots WHERE bot_id = {placeholder}",
        (BOT_ID, live_cred_id, now, BOT_ID)
    )
    print(f"INSERTED bot_credentials: {BOT_ID} -> {live_cred_id}")

# 4. Also ensure the bot itself is flagged is_live=True and broker_account_id is correct
cur.execute(
    f"UPDATE user_bots SET is_live = {'TRUE' if DATABASE_BACKEND == 'postgres' else '1'}, broker_account_id = {placeholder} WHERE bot_id = {placeholder}",
    (f'Exness_{LIVE_ACCOUNT}', BOT_ID)
)
print(f"Updated user_bots: is_live=True, broker_account_id=Exness_{LIVE_ACCOUNT}")

conn.commit()
conn.close()
print("Done. Restart the backend for the change to take effect.")
