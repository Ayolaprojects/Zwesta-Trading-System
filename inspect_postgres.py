import urllib.parse
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = 'postgresql://zwesta_admin:Zwesta%40Trading2026%21@localhost:5432/zwesta_trading'
print('Connecting to', DATABASE_URL)
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor(cursor_factory=RealDictCursor)
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
rows = cur.fetchall()
print('TABLES:')
for row in rows:
    print(' ', row['table_name'])

bot_ids = ['1780678113048', '178090663839']
for table in [row['table_name'] for row in rows]:
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s", (table,))
    cols = cur.fetchall()
    text_cols = [c['column_name'] for c in cols if c['data_type'] in ('text', 'character varying', 'varchar', 'bigint', 'integer')]
    for col in text_cols:
        for bot_id in bot_ids:
            try:
                cur.execute(f"SELECT COUNT(*) AS cnt FROM {table} WHERE {col} = %s", (bot_id,))
                cnt = cur.fetchone()['cnt']
                if cnt:
                    print(f"{table}.{col} exact {bot_id}: {cnt}")
            except Exception:
                pass
conn.close()
