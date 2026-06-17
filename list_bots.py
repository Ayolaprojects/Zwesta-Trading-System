import os
from dotenv import load_dotenv
load_dotenv('.env')
import os
from dotenv import load_dotenv
load_dotenv('.env')
import psycopg2
from psycopg2.extras import RealDictCursor

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
cursor = conn.cursor()

search_id = '1781308107019'

# Get all tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r['tablename'] for r in cursor.fetchall()]

print(f'Searching ALL tables for: {search_id}\n')
found_any = False

for tbl in tables:
    try:
        cursor.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_name=%s
            AND data_type IN ('text','character varying','bigint','numeric','integer','json','jsonb','uuid')
            ORDER BY ordinal_position
        """, (tbl,))
        cols = cursor.fetchall()
        if not cols:
            continue
        conditions = ' OR '.join([f"CAST({col['column_name']} AS TEXT) LIKE '%{search_id}%'" for col in cols])
        cursor.execute(f'SELECT * FROM "{tbl}" WHERE {conditions} LIMIT 5')
        rows = cursor.fetchall()
        if rows:
            found_any = True
            print(f'\n=== FOUND IN: {tbl} ({len(rows)} rows) ===')
            for row in rows:
                for k, v in dict(row).items():
                    if v is not None and search_id in str(v):
                        print(f'   {k} = {str(v)[:300]}')
    except Exception as e:
        print(f'[skip {tbl}]: {e}')

if not found_any:
    print('NOT FOUND in any table.')
    print('\nMost recently created bots:')
    cursor.execute("SELECT bot_id, total_profit, status, created_at FROM user_bots ORDER BY created_at DESC LIMIT 5")
    for r in cursor.fetchall():
        print(f'  {r["bot_id"]} | ${r["total_profit"]} | {r["status"]} | {r["created_at"]}')
    print('\nMost recent Binance orders:')
    cursor.execute("SELECT * FROM binance_orders ORDER BY created_at DESC LIMIT 5")
    for r in cursor.fetchall():
        print(f'  {dict(r)}')
    print('\nWorker bot queue:')
    cursor.execute("SELECT * FROM worker_bot_queue ORDER BY created_at DESC LIMIT 5")
    for r in cursor.fetchall():
        print(f'  {dict(r)}')
    print('\nWorker bot assignments:')
    cursor.execute("SELECT * FROM worker_bot_assignments LIMIT 5")
    for r in cursor.fetchall():
        print(f'  {dict(r)}')

conn.close()