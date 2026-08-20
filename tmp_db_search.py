import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)
sys.path.insert(0, os.getcwd())
from runtime_infrastructure import get_database_url, using_postgres

url = get_database_url()
print('DATABASE_URL=', url)
print('USING_POSTGRES=', using_postgres())

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=RealDictCursor)
search = '1786110335759'
queries = [
    ('trades exact', "SELECT trade_id, bot_id, ticket, symbol, status, trade_data FROM trades WHERE ticket = %s LIMIT 5"),
    ('trades ticket-like', "SELECT trade_id, bot_id, ticket, symbol, status, trade_data FROM trades WHERE ticket::text ILIKE %s LIMIT 20"),
    ('trades trade_data contains string', "SELECT trade_id, bot_id, ticket, symbol, status, trade_data FROM trades WHERE trade_data::text ILIKE %s LIMIT 20"),
    ('user_bots runtime_state contains string', "SELECT bot_id, name, enabled, status, runtime_state::text FROM user_bots WHERE runtime_state::text ILIKE %s LIMIT 50"),
    ('user_bots bot_id-like', "SELECT bot_id, name, enabled, status FROM user_bots WHERE bot_id ILIKE %s LIMIT 50"),
]
for label, q in queries:
    print('\n---', label, '---')
    cur.execute(q, ("%" + search + "%",))
    rows = cur.fetchall()
    print('rows', len(rows))
    for row in rows:
        print(row)
cur.close()
conn.close()
