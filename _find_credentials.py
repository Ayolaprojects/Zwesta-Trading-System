#!/usr/bin/env python3
"""Find Exness credentials and users"""
import sqlite3
import json

DB_PATH = r'C:\zwesta-trader\zwesta_trader.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 80)
print("Finding Exness Credentials")
print("=" * 80)

# Find all Exness credentials
cursor.execute("""
    SELECT credential_id, user_id, broker_name, account_number, server, is_live, is_active
    FROM broker_credentials
    WHERE broker_name LIKE '%Exness%'
    ORDER BY created_at DESC
    LIMIT 10
""")

rows = cursor.fetchall()

if not rows:
    print("\n❌ No Exness credentials found")
    print("\nSearching for ANY broker credentials...")
    cursor.execute("""
        SELECT credential_id, user_id, broker_name, account_number, server, is_live
        FROM broker_credentials
        ORDER BY created_at DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()

print(f"\nFound {len(rows)} credential(s):\n")

for row in rows:
    if len(row) >= 7:
        cred_id, user_id, broker, account, server, is_live, is_active = row[:7]
        print(f"Credential ID: {cred_id}")
        print(f"User ID: {user_id}")
        print(f"Broker: {broker}")
        print(f"Account: {account}")
        print(f"Server: {server}")
        print(f"Type: {'LIVE' if is_live else 'DEMO'}")
        if len(row) >= 7:
            print(f"Active: {'Yes' if is_active else 'No'}")
        print("-" * 80)
    else:
        cred_id, user_id, broker, account, server, is_live = row[:6]
        print(f"Credential ID: {cred_id}")
        print(f"User ID: {user_id}")
        print(f"Broker: {broker}")
        print(f"Account: {account}")
        print(f"Server: {server}")
        print(f"Type: {'LIVE' if is_live else 'DEMO'}")
        print("-" * 80)

# Find all users
print("\n" + "=" * 80)
print("All Users")
print("=" * 80)

cursor.execute("SELECT user_id, email, name FROM users ORDER BY created_at DESC LIMIT 10")
users = cursor.fetchall()

for user in users:
    print(f"User ID: {user[0]}")
    print(f"Email: {user[1] if len(user) > 1 else 'N/A'}")
    print(f"Name: {user[2] if len(user) > 2 else 'N/A'}")
    print("-" * 80)

conn.close()
