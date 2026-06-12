import os
import sqlite3
import uuid
from datetime import datetime, timedelta

from runtime_infrastructure import build_sqlite_connection, get_database_path, get_database_url, using_postgres

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def get_connection():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError('psycopg2 is required for PostgreSQL mode')
        database_url = get_database_url()
        if not database_url:
            raise RuntimeError('DATABASE_URL is required for PostgreSQL mode')
        return psycopg2.connect(database_url), 'postgres'
    return build_sqlite_connection(database_path=get_database_path()), 'sqlite'


def resolve_user_id(cursor, backend: str) -> str:
    configured_user = str(os.getenv('DEBUG_SESSION_USER_ID', '') or '').strip()
    if configured_user:
        if backend == 'postgres':
            cursor.execute('SELECT user_id FROM users WHERE user_id = %s LIMIT 1', (configured_user,))
        else:
            cursor.execute('SELECT user_id FROM users WHERE user_id = ? LIMIT 1', (configured_user,))
        row = cursor.fetchone()
        if row:
            return row[0]

    cursor.execute('SELECT user_id FROM users ORDER BY created_at DESC LIMIT 1')
    row = cursor.fetchone()
    if not row:
        raise RuntimeError('No users found. Create a user first or set DEBUG_SESSION_USER_ID to an existing user_id.')
    return row[0]


conn, backend = get_connection()
cursor = conn.cursor()

test_session_token = str(os.getenv('DEBUG_SESSION_TOKEN', 'test-session-token-123') or 'test-session-token-123').strip()
test_user_id = resolve_user_id(cursor, backend)

session_id = str(uuid.uuid4())
created_at = datetime.now().isoformat()
expiry = (datetime.now() + timedelta(hours=24)).isoformat()

if backend == 'postgres':
    cursor.execute('DELETE FROM user_sessions WHERE token = %s', (test_session_token,))
    cursor.execute(
        '''
        INSERT INTO user_sessions (session_id, user_id, token, created_at, expires_at, ip_address, user_agent, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''',
        (session_id, test_user_id, test_session_token, created_at, expiry, '127.0.0.1', 'test-client', True),
    )
    cursor.execute('SELECT session_id FROM user_sessions WHERE token = %s', (test_session_token,))
else:
    cursor.execute('DELETE FROM user_sessions WHERE token = ?', (test_session_token,))
    cursor.execute(
        '''
        INSERT INTO user_sessions (session_id, user_id, token, created_at, expires_at, ip_address, user_agent, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (session_id, test_user_id, test_session_token, created_at, expiry, '127.0.0.1', 'test-client', 1),
    )
    cursor.execute('SELECT session_id FROM user_sessions WHERE token = ?', (test_session_token,))

conn.commit()
session = cursor.fetchone()
conn.close()

if session:
    print('[OK] Test session created successfully')
    print(f'    Backend: {backend.upper()}')
    print(f'    User ID: {test_user_id}')
    print(f'    Session Token: {test_session_token}')
    print(f'    Session ID: {session_id}')
    print(f'    Expires: {expiry}')
else:
    print('[ERROR] Failed to create test session')
