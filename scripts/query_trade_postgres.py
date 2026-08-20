import sys
import json
import os
# ensure workspace module path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)

from runtime_infrastructure import get_database_url

try:
    import psycopg2
    import psycopg2.extras
except Exception as e:
    print('ERROR: missing psycopg2:', e)
    sys.exit(2)

ticket = sys.argv[1] if len(sys.argv) > 1 else '1786110335759'
url = get_database_url()
if not url:
    print('No DATABASE_URL configured')
    sys.exit(1)

try:
    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT trade_id, bot_id, ticket, symbol, price, profit, status, trade_data FROM trades WHERE ticket = %s LIMIT 1", (ticket,))
    row = cur.fetchone()
    if not row:
        print('NOT FOUND')
    else:
        # print compact JSON
        row['trade_data'] = row.get('trade_data')
        print(json.dumps(row, default=str))
    cur.close()
    conn.close()
except Exception as e:
    print('DB ERROR:', e)
    sys.exit(3)

# If not found in trades, try to find ticket inside persisted runtime_state in user_bots
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE runtime_state::text ILIKE %s LIMIT 5", (f'%{ticket}%',))
    rows = cur.fetchall()
    if rows:
        for r in rows:
            bot_id = r[0]
            try:
                rs = r[1]
                print('RUNTIME_MATCH', bot_id, json.dumps(rs, default=str)[:1000])
            except Exception:
                print('RUNTIME_MATCH', bot_id, str(r[1])[:1000])
    else:
        print('NO_RUNTIME_MATCH')
    cur.close()
    conn.close()
except Exception as e:
    print('RUNTIME_QUERY_ERROR', e)
