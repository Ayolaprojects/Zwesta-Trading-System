#!/usr/bin/env python3
"""Check bot-credential linkage"""

import sqlite3
from runtime_infrastructure import build_sqlite_connection, get_database_path, get_database_url, using_postgres

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def get_connection():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError('psycopg2 is required for PostgreSQL mode')
        database_url = get_database_url()
        if not database_url:
            raise RuntimeError('DATABASE_URL is required for PostgreSQL mode')
        return psycopg2.connect(database_url), 'postgres'
    return build_sqlite_connection(database_path=get_database_path(), row_factory=True), 'sqlite'

conn, backend = get_connection()
if backend == 'sqlite':
    conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== CHECKING BOT CREDENTIALS LINKAGE ===\n")
print(f"Backend: {backend.upper()}\n")


def row_get(row, key, index):
    if hasattr(row, 'keys'):
        return row[key]
    return row[index]

# Check user_bots
cursor.execute("SELECT bot_id, broker_account_id FROM user_bots")
bots = cursor.fetchall()
print("User Bots:")
for bot in bots:
    print(f"  {str(row_get(bot, 'bot_id', 0)):30s} | broker_account_id: {row_get(bot, 'broker_account_id', 1)}")

# Check bot_credentials
cursor.execute("SELECT bot_id, credential_id, user_id FROM bot_credentials")
bot_creds = cursor.fetchall()
print(f"\nBot Credentials Links:")
if bot_creds:
    for bc in bot_creds:
        print(f"  {str(row_get(bc, 'bot_id', 0)):30s} -> {row_get(bc, 'credential_id', 1)}")
else:
    print("  ❌ NO LINKS FOUND")

# Check broker_credentials
cursor.execute("SELECT credential_id, broker_name, account_number FROM broker_credentials")
creds = cursor.fetchall()
print(f"\nBroker Credentials:")
for cred in creds:
    credential_id = str(row_get(cred, 'credential_id', 0) or '')
    broker_name = str(row_get(cred, 'broker_name', 1) or '')
    account_number = row_get(cred, 'account_number', 2)
    print(f"  {credential_id[:10]:10s} | {broker_name:15s} | Account: {account_number}")

conn.close()

print("\n=== ANALYSIS ===")
print("✓ If bot_credentials table is EMPTY → bots won't find their credentials")
print("✓ If credentialId in bots isn't in broker_credentials → credentials not found")
