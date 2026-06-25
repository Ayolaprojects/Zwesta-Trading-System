import sqlite3

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Find all bot IDs
cur.execute("SELECT bot_id, user_id FROM user_bots")
bots = {row[0]: row[1] for row in cur.fetchall()}
print(f"Found {len(bots)} bots in SQLite")

# Find all credentials
cur.execute("SELECT credential_id, broker_name, account_number FROM broker_credentials WHERE is_active=1")
creds = cur.fetchall()
print(f"\nActive credentials:")
for c in creds:
    print(f"  {c[1]}({c[0][:8]}...) account={c[2]}")

# Link any bots without credentials to the Exness demo credential
exness_demo_cred = 'b7cc78a2-7096-4fc9-aa80-6d6eb2c06f88'  # From .env EXNESS_DEMO_ACCOUNT

for bot_id in bots:
    cur.execute("SELECT 1 FROM bot_credentials WHERE bot_id = ?", (bot_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO bot_credentials (bot_id, credential_id, user_id, created_at) VALUES (?, ?, ?, ?)",
                    (bot_id, exness_demo_cred, bots[bot_id], '2026-06-24T16:00:00'))
        print(f"Linked {bot_id} to Exness demo credential")

conn.commit()
conn.close()
print("\nDone")