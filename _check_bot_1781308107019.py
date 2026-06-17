import psycopg2

conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading')
cur = conn.cursor()
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
print('Tables:', [r[0] for r in cur.fetchall()])
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%bot%'")
print('Bot tables:', [r[0] for r in cur.fetchall()])
conn.close()
