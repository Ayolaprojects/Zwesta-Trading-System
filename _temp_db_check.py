import psycopg2, psycopg2.extras

conn = psycopg2.connect("postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading")
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get users table columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
cols = [r['column_name'] for r in cur.fetchall()]
print("users columns:", cols)

# Get all users
cur.execute("SELECT * FROM users LIMIT 20")
print("\n--- USERS ---")
for r in cur.fetchall():
    print(dict(r))

# Bot credentials linkage
print("\n--- BOT + BROKER LINKAGE ---")
cur.execute("""
    SELECT bc.bot_id, bc.credential_id, bcr.broker_name, bcr.account_number,
           ub.status, ub.enabled, ub.is_live, ub.user_id, ub.created_at
    FROM bot_credentials bc
    JOIN broker_credentials bcr ON bcr.credential_id = bc.credential_id
    JOIN user_bots ub ON ub.bot_id = bc.bot_id
    ORDER BY ub.created_at DESC LIMIT 20
""")
for r in cur.fetchall():
    print(dict(r))

# All broker credentials
print("\n--- BROKER CREDENTIALS ---")
cur.execute("SELECT credential_id, user_id, broker_name, account_number, is_active, created_at FROM broker_credentials ORDER BY created_at DESC LIMIT 20")
for r in cur.fetchall():
    print(dict(r))

conn.close()
