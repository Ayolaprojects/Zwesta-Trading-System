import sqlite3
import os

db_path = r'zwesta_trading.db'

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check if the Exness demo credential exists
cur.execute("SELECT credential_id FROM broker_credentials WHERE broker_name='Exness'")
if cur.fetchone():
    print("Exness credential already exists")
else:
    # Add the Exness demo credential from .env
    cur.execute("""
        INSERT INTO broker_credentials 
        (credential_id, user_id, broker_name, account_number, password, server, is_live, is_active, created_at, account_currency)
        VALUES (?, ?, ?, ?, ?, ?, 0, 1, '2026-06-24T16:00:00', 'USD')
    """, (
        'b7cc78a2-7096-4fc9-aa80-6d6eb2c06f88',  # credential_id
        '8e74db37-fd1e-4c57-87c4-ad3b64012ecf',  # user_id (test user)
        'Exness',
        '435760376',  # EXNESS_DEMO_ACCOUNT from .env
        'Zwesta@1985',  # EXNESS_DEMO_PASSWORD from .env
        'Exness-MT5Trial9'  # EXNESS_DEMO_SERVER from .env
    ))
    conn.commit()
    print("Added Exness demo credential to SQLite")

conn.close()