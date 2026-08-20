import os
import sys
import types

# Prevent .env auto-loading from overriding our test environment.
os.environ['ZWESTA_SKIP_PYTHON_REEXEC'] = '1'
os.environ['DATABASE_BACKEND'] = 'sqlite'
os.environ['DATABASE_URL'] = ''
os.environ['DATABASE_PATH'] = os.path.join(r'C:\zwesta-trader\Zwesta Flutter App', 'zwesta_trading_test.db')
os.environ['USE_FLASK_DEV'] = '1'
os.environ['FLASK_DEBUG'] = '0'

# Mock dotenv before importing backend runtime infrastructure
sys.path.insert(0, os.getcwd())
import types
sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)

import multi_broker_backend_updated as backend

# Remove any stale test DB
try:
    if os.path.exists(os.environ['DATABASE_PATH']):
        os.remove(os.environ['DATABASE_PATH'])
except Exception:
    pass

conn = backend.get_db_connection()
cursor = conn.cursor()
backend.ensure_user_preferences_table(cursor)
# Create minimal broker_credentials table for switch-mode lookup
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

# Insert a live and demo credential row for test_user
cursor.execute('INSERT OR REPLACE INTO broker_credentials (credential_id, user_id, broker_name, account_number, server, is_live, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
               ('cred_live_123', 'test_user', 'Exness', '12345', 'Exness-Real', 1, 1, '2026-01-01T00:00:00', '2026-01-01T00:00:00'))
cursor.execute('INSERT OR REPLACE INTO broker_credentials (credential_id, user_id, broker_name, account_number, server, is_live, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
               ('cred_demo_123', 'test_user', 'Exness', '298997455', 'Exness-MT5Trial9', 0, 1, '2026-01-01T00:00:00', '2026-01-01T00:00:00'))
conn.commit()
conn.close()

# Test live switch with explicit account/server
ctx = backend.app.test_request_context('/api/user/switch-mode', method='POST', json={'mode': 'LIVE', 'account': '12345', 'server': 'Exness-Real'})
ctx.push()
try:
    request = backend.request
    request.user_id = 'test_user'
    resp = backend.switch_trading_mode.__wrapped__()
    print('LIVE status', resp[1])
    print(resp[0].json)
finally:
    ctx.pop()

# Test demo switch, preserving live values
ctx = backend.app.test_request_context('/api/user/switch-mode', method='POST', json={'mode': 'DEMO'})
ctx.push()
try:
    request = backend.request
    request.user_id = 'test_user'
    resp = backend.switch_trading_mode.__wrapped__()
    print('DEMO status', resp[1])
    print(resp[0].json)
finally:
    ctx.pop()

# verify get_trading_mode returns preserved live credentials
ctx = backend.app.test_request_context('/api/user/trading-mode', method='GET', headers={'X-User-ID': 'test_user'})
ctx.push()
try:
    resp = backend.get_trading_mode.__wrapped__()
    print('TRADING MODE status', resp[1])
    print(resp[0].json)
finally:
    ctx.pop()

# verify persisted values
conn = backend.get_db_connection()
cursor = conn.cursor()
cursor.execute('SELECT trading_mode, live_account, live_server FROM user_preferences WHERE user_id = ?', ('test_user',))
print('saved', cursor.fetchone())
conn.close()
