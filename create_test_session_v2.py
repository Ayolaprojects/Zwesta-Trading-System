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


def fetch_existing_user_id(cursor, backend: str) -> str:
    preferred_user = str(os.getenv('DEBUG_SESSION_USER_ID', '') or '').strip()
    if preferred_user:
        if backend == 'postgres':
            cursor.execute('SELECT user_id FROM users WHERE user_id = %s LIMIT 1', (preferred_user,))
        else:
            cursor.execute('SELECT user_id FROM users WHERE user_id = ? LIMIT 1', (preferred_user,))
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

user_id = fetch_existing_user_id(cursor, backend)
session_id = str(uuid.uuid4())
token = f'debug_token_{uuid.uuid4().hex[:32]}'
now = datetime.now().isoformat()
expires = (datetime.now() + timedelta(days=30)).isoformat()

if backend == 'postgres':
    cursor.execute(
        '''
        INSERT INTO user_sessions (session_id, user_id, token, created_at, expires_at, ip_address, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''',
        (session_id, user_id, token, now, expires, '127.0.0.1', True),
    )
else:
    cursor.execute(
        '''
        INSERT INTO user_sessions (session_id, user_id, token, created_at, expires_at, ip_address, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (session_id, user_id, token, now, expires, '127.0.0.1', 1),
    )

conn.commit()
print('✅ Session created for test user!')
print(f'Backend: {backend.upper()}')
print(f'User ID: {user_id}')
print(f'Token: {token}')
print()
print('Use this header in API requests:')
print(f'X-Session-Token: {token}')

conn.close()
