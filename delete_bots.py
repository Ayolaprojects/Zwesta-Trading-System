import psycopg2

DATABASE_URL = "postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading"

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()
cur.execute("DELETE FROM user_bots")
cur.execute("DELETE FROM bot_credentials")
cur.execute("DELETE FROM trades")
conn.commit()
print(f"Deleted all bots, credentials, and trades")
conn.close()