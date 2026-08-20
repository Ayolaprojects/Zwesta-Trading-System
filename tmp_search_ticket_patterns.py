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
conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=RealDictCursor)
pattern='17861'
print('pattern', pattern)
print('--- bot_id pattern ---')
cur.execute("SELECT bot_id, name, enabled, status FROM user_bots WHERE bot_id ILIKE %s LIMIT 50", ('%'+pattern+'%',))
for row in cur.fetchall():
    print(row)
print('--- trade_id pattern ---')
cur.execute("SELECT trade_id, bot_id, ticket, symbol, status FROM trades WHERE trade_id ILIKE %s LIMIT 50", ('%'+pattern+'%',))
for row in cur.fetchall():
    print(row)
print('--- ticket pattern ---')
cur.execute("SELECT trade_id, bot_id, ticket, symbol, status FROM trades WHERE ticket::text ILIKE %s LIMIT 50", ('%'+pattern+'%',))
for row in cur.fetchall():
    print(row)
print('--- runtime_state sample with bot_id pattern ---')
cur.execute("SELECT bot_id, name, runtime_state::text FROM user_bots WHERE runtime_state::text ILIKE %s LIMIT 50", ('%'+pattern+'%',))
for row in cur.fetchall():
    print(row['bot_id'], row['name'], row['runtime_state'][:400])
cur.close(); conn.close()
