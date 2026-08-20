import os
import sys
import json
import ast
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(r'c:\zwesta-trader\Zwesta Flutter App\vps_app_package\.env', override=True)
from runtime_infrastructure import get_database_url

import psycopg2
import psycopg2.extras

url = get_database_url()
if not url:
    print('No DATABASE_URL configured')
    sys.exit(1)

conn = psycopg2.connect(url)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT bot_id, user_id, status, runtime_state FROM user_bots WHERE runtime_state IS NOT NULL LIMIT 500")
rows = cur.fetchall()

candidates = []
for r in rows:
    text = r['runtime_state']
    if not text:
        continue
    try:
        state = json.loads(text)
    except Exception:
        try:
            state = ast.literal_eval(text)
        except Exception:
            continue
    if not isinstance(state, dict):
        continue
    if 'Binance' not in text and 'binance' not in text:
        continue
    if 'futures' not in text and 'FUTURES' not in text and 'futures' not in text.lower():
        continue
    tracked = state.get('tracked') or state.get('open_positions') or {}
    if isinstance(tracked, dict):
        ticket_count = len(tracked)
    else:
        ticket_count = len(tracked) if isinstance(tracked, list) else 0
    candidate = {
        'bot_id': r['bot_id'],
        'user_id': r['user_id'],
        'status': r['status'],
        'ticket_count': ticket_count,
        'tracked_keys': list(tracked.keys()) if isinstance(tracked, dict) else None,
    }
    # optionally print one sample
    sample = None
    if isinstance(tracked, dict) and tracked:
        first_ticket, first_state = next(iter(tracked.items()))
        symbol = first_state.get('symbol') if isinstance(first_state, dict) else None
        candidate['sample_ticket'] = first_ticket
        candidate['sample_symbol'] = symbol
    candidates.append(candidate)

print('Found', len(candidates), 'candidate runtime states with Binance+futures')
for c in candidates:
    print(json.dumps(c))

cur.close()
conn.close()
