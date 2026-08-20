import os
import sys
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)
from runtime_infrastructure import get_database_url

url = get_database_url()
if not url:
    print('No DATABASE_URL configured')
    sys.exit(1)

conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute(
    "SELECT bot_id, user_id, status, runtime_state FROM user_bots WHERE runtime_state IS NOT NULL LIMIT 200"
)
rows = cur.fetchall()
for r in rows:
    text = str(r['runtime_state'])
    if 'Binance' in text or 'futures' in text or 'DEMO' in text:
        print(json.dumps({
            'bot_id': r['bot_id'],
            'user_id': r['user_id'],
            'status': r['status'],
            'has_binance': 'Binance' in text,
            'has_futures': 'futures' in text,
            'has_demo': 'DEMO' in text,
        }))
cur.close()
conn.close()
