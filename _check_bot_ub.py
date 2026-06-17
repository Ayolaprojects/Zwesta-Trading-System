import psycopg2

conn = psycopg2.connect('postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading')
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='user_bots' ORDER BY ordinal_position")
print('Columns:', [r[0] for r in cur.fetchall()])

cur.execute("SELECT bot_id, status, enabled, symbols, total_profit FROM user_bots WHERE bot_id LIKE '%1781308107019%'")
rows = cur.fetchall()
print('Match:', rows if rows else 'NOT FOUND')

cur.execute("SELECT COUNT(*) FROM user_bots")
print('Total user_bots:', cur.fetchone()[0])

cur.execute("SELECT bot_id, status, enabled, total_profit FROM user_bots ORDER BY created_at DESC LIMIT 5")
print('Latest 5:')
for r in cur.fetchall():
    print(' ', r)

conn.close()
