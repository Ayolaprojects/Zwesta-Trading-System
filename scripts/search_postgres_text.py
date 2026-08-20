import os
import sys
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ensure workspace module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Load VPS .env for correct Postgres connection
load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)
from runtime_infrastructure import get_database_url

if len(sys.argv) < 2:
    print('Usage: search_postgres_text.py <search_string>')
    sys.exit(1)

search_text = sys.argv[1]
url = get_database_url()
if not url:
    print('No DATABASE_URL configured')
    sys.exit(1)

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') AND table_type='BASE TABLE'")
rows = cur.fetchall()
found = []
for schema, table in rows:
    try:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema=%s AND table_name=%s", (schema, table))
        cols = cur.fetchall()
        text_cols = [c for c,d in cols if d in ('character varying','text','json','jsonb')]
        if not text_cols:
            continue
        for col in text_cols:
            colname = col
            try:
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE CAST({colname} AS TEXT) ILIKE %s", (f'%{search_text}%',))
                count = cur.fetchone()[0]
                if count > 0:
                    found.append((schema, table, colname, count))
            except Exception:
                continue
    except Exception:
        continue
for item in found:
    print('FOUND', item)
if not found:
    print('NONE')
cur.close()
conn.close()
