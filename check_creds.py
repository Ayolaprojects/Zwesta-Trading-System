import psycopg2
conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026!@localhost:5432/zwesta_trading')
cur = conn.cursor()
cur.execute("SELECT credential_id, user_id, broker_name, is_live, account_number, server FROM broker_credentials WHERE broker_name ILIKE '%exness%' LIMIT 5")
for row in cur.fetchall():
    print(row)
conn.close()