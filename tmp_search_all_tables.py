import os
import sys
import json
from dotenv import load_dotenv
load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)
sys.path.insert(0, os.getcwd())
from runtime_infrastructure import get_database_url
import psycopg2
from psycopg2.extras import RealDictCursor

url = get_database_url()
print('DATABASE_URL=', url)
conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=RealDictCursor)
pattern = '1786110335759'
cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND data_type IN ('text','character varying','json','jsonb') ORDER BY table_name, column_name")
cols = cur.fetchall()
print('checked columns', len(cols))
for table, column, datatype in cols:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {column}::text ILIKE %s", ('%' + pattern + '%',))
        count = cur.fetchone()['count']
        if count and int(count) > 0:
            print('FOUND', table, column, datatype, count)
            cur.execute(f"SELECT {column} FROM {table} WHERE {column}::text ILIKE %s LIMIT 5", ('%' + pattern + '%',))
            for r in cur.fetchall():
                print('  ', r[column])
    except Exception:
        pass
cur.close()
conn.close()
