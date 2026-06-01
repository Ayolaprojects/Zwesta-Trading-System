#!/usr/bin/env python3
"""Fix Exness credentials by setting broker_name"""
import sqlite3

DB_PATH = r'C:\zwesta-trader\zwesta_trader.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("FIXING EXNESS CREDENTIALS")
print("=" * 80)

# Update credentials with Exness servers
cursor.execute("""
    UPDATE broker_credentials
    SET broker_name = 'Exness'
    WHERE server LIKE '%Exness%' AND (broker_name IS NULL OR broker_name = '')
""")

rows_updated = cursor.rowcount
conn.commit()

print(f"\n✅ Updated {rows_updated} credential(s)")

# Verify
cursor.execute("""
    SELECT credential_id, broker_name, account_number, server, is_live
    FROM broker_credentials
    WHERE broker_name = 'Exness'
""")

results = cursor.fetchall()

print(f"\nExness Credentials Found: {len(results)}")
for row in results:
    cred_id, broker, account, server, is_live = row
    print(f"\n  Credential ID: {cred_id}")
    print(f"  Broker: {broker}")
    print(f"  Account: {account}")
    print(f"  Server: {server}")
    print(f"  Type: {'LIVE' if is_live else 'DEMO'}")

conn.close()

print("\n" + "=" * 80)
print("✅ CREDENTIALS FIXED!")
print("=" * 80)
print("\nNow run: python _create_multi_symbol_pyramid_bot.py")
