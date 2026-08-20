import os, sys, json
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

print('--- open trades sample ---')
cur.execute("SELECT trade_id, bot_id, ticket, symbol, status, trade_data, created_at, updated_at FROM trades WHERE status = 'open' ORDER BY updated_at DESC LIMIT 20")
for row in cur.fetchall():
    print({
        'trade_id': row['trade_id'],
        'bot_id': row['bot_id'],
        'ticket': row['ticket'],
        'symbol': row['symbol'],
        'status': row['status'],
        'created_at': str(row['created_at']),
        'updated_at': str(row['updated_at']),
        'trade_data_keys': list(row['trade_data'].keys()) if isinstance(row['trade_data'], dict) else None,
    })

print('\n--- active bots sample ---')
cur.execute("SELECT bot_id, name, enabled, status, runtime_state::text FROM user_bots ORDER BY updated_at DESC LIMIT 50")
for row in cur.fetchall():
    raw = row['runtime_state']
    runtime = None
    try:
        runtime = json.loads(raw) if raw else {}
    except Exception as e:
        runtime = {'_parse_error': str(e)}
    open_positions = runtime.get('open_positions') or runtime.get('tracked') or {}
    open_count = len(open_positions) if isinstance(open_positions, dict) else 0
    print({
        'bot_id': row['bot_id'],
        'name': row['name'],
        'enabled': row['enabled'],
        'status': row['status'],
        'open_positions': open_count,
        'top_keys': list(open_positions.keys())[:5] if isinstance(open_positions, dict) else None,
        'broker': runtime.get('brokerName') or runtime.get('broker_name') or runtime.get('accountNumber') or runtime.get('account_number'),
        'market': runtime.get('binanceMarket') or runtime.get('market') or runtime.get('brokerMarket'),
    })
print('\n--- search runtime_state for numeric IDs ---')
cur.execute("SELECT bot_id, name, runtime_state::text FROM user_bots WHERE runtime_state::text ILIKE '%17861%' LIMIT 100")
for row in cur.fetchall():
    print('MATCH BOT', row['bot_id'], row['name'], row['runtime_state'][:300])

cur.close()
conn.close()
