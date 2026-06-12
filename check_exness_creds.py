#!/usr/bin/env python3
"""Check Exness credentials in database"""

import sqlite3
import json
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

conn, backend = get_connection()
cursor = conn.cursor()

print(f"Backend: {backend.upper()}")

# Check table structure
print("=== BROKER_CREDENTIALS TABLE STRUCTURE ===")
if backend == 'postgres':
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'broker_credentials'
        ORDER BY ordinal_position
        """
    )
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]} ({col[1]})")
else:
    cursor.execute("PRAGMA table_info(broker_credentials)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

# Check for Exness data
print("\n=== EXNESS CREDENTIALS IN DATABASE ===")
try:
    cursor.execute("SELECT * FROM broker_credentials WHERE broker_name LIKE '%Exness%' LIMIT 5")
    rows = cursor.fetchall()
    print(f"Found {len(rows)} Exness records")
    
    if rows:
        # Get column names
        cursor.execute("SELECT * FROM broker_credentials WHERE broker_name LIKE '%Exness%' LIMIT 1")
        col_names = [description[0] for description in cursor.description]
        print(f"\nColumns: {col_names}")
        
        for row in rows:
            print(f"\nRecord: {row}")
            
except Exception as e:
    print(f"Error: {e}")

conn.close()
