import os, sys, types

os.environ['ZWESTA_SKIP_PYTHON_REEXEC'] = '1'
os.environ['DATABASE_BACKEND'] = 'sqlite'
os.environ['DATABASE_URL'] = ''
os.environ['DATABASE_PATH'] = os.path.join(r'C:\zwesta-trader\Zwesta Flutter App', 'zwesta_trading_test.db')
os.environ['USE_FLASK_DEV'] = '1'
os.environ['FLASK_DEBUG'] = '0'

sys.path.insert(0, os.getcwd())
import types
sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)
import multi_broker_backend_updated as backend

# Remove stale DB
try:
    os.remove(os.environ['DATABASE_PATH'])
except Exception:
    pass

conn = backend.get_db_connection()
cursor = conn.cursor()
backend.ensure_user_preferences_table(cursor)
cursor.execute('''
CREATE TABLE IF NOT EXISTS broker_credentials (
    credential_id TEXT PRIMARY KEY,
    user_id TEXT,
    broker_name TEXT,
    account_number TEXT,
    server TEXT,
    is_live INTEGER,
    is_active INTEGER,
    created_at TEXT,
    updated_at TEXT
)
''')
conn.commit()

cursor.execute('INSERT OR REPLACE INTO broker_credentials (credential_id, user_id, broker_name, account_number, server, is_live, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
               ('cred_live_123', 'test_user', 'Exness', '12345', 'Exness-Real', 1, 1, '2026-01-01T00:00:00', '2026-01-01T00:00:00'))
cursor.execute('INSERT OR REPLACE INTO broker_credentials (credential_id, user_id, broker_name, account_number, server, is_live, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
               ('cred_demo_123', 'test_user', 'Exness', '298997455', 'Exness-MT5Trial9', 0, 1, '2026-01-01T00:00:00', '2026-01-01T00:00:00'))
conn.commit()
conn.close()

conn = backend.get_db_connection()
cur = conn.cursor()
cur.execute('SELECT * FROM broker_credentials')
print('initial broker creds:', cur.fetchall())
conn.close()

ctx = backend.app.test_request_context('/api/user/switch-mode', method='POST', json={'mode': 'LIVE', 'account': '12345', 'server': 'Exness-Real'})
ctx.push()
try:
    request = backend.request
    request.user_id = 'test_user'
    resp = backend.switch_trading_mode.__wrapped__()
    print('LIVE resp status', resp[1])
    print('LIVE resp json', resp[0].json)
finally:
    ctx.pop()

conn = backend.get_db_connection()
cur = conn.cursor()
cur.execute('SELECT * FROM user_preferences')
print('after LIVE user_preferences:', cur.fetchall())
conn.close()

ctx = backend.app.test_request_context('/api/user/switch-mode', method='POST', json={'mode': 'DEMO'})
ctx.push()
try:
    request = backend.request
    request.user_id = 'test_user'
    resp = backend.switch_trading_mode.__wrapped__()
    print('DEMO resp status', resp[1])
    print('DEMO resp json', resp[0].json)
finally:
    ctx.pop()

conn = backend.get_db_connection()
cur = conn.cursor()
cur.execute('SELECT * FROM user_preferences')
print('after DEMO user_preferences:', cur.fetchall())
conn.close()
