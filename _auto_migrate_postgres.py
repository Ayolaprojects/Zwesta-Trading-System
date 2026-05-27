"""
Automatic SQLite to PostgreSQL Migration
Mirrors exact schema from SQLite and migrates all data
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import json

# Configuration
SQLITE_DB_PATH = r'C:\backend\zwesta_trading.db'
POSTGRES_CONFIG = {
    'host': 'localhost',
    'database': 'zwesta_trading',
    'user': 'zwesta_admin',
    'password': 'Zwesta@Trading2026!',
    'port': 5432
}

# SQLite to PostgreSQL type mapping
TYPE_MAPPING = {
    'TEXT': 'TEXT',
    'INTEGER': 'INTEGER',
    'REAL': 'DOUBLE PRECISION',
    'BOOLEAN': 'BOOLEAN',
    'BLOB': 'BYTEA',
    'DATETIME': 'TIMESTAMP'
}

def sqlite_to_postgres_type(sqlite_type):
    """Convert SQLite type to PostgreSQL type"""
    sqlite_type_upper = sqlite_type.upper()
    for sql_type, pg_type in TYPE_MAPPING.items():
        if sql_type in sqlite_type_upper:
            return pg_type
    return 'TEXT'  # Default

def get_sqlite_schema(sqlite_conn, table_name):
    """Get schema for a SQLite table"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def create_postgres_table_from_sqlite(pg_conn, sqlite_conn, table_name):
    """Create PostgreSQL table that mirrors SQLite table exactly"""
    pg_cursor = pg_conn.cursor()
    
    # Get SQLite schema
    schema = get_sqlite_schema(sqlite_conn, table_name)
    
    # Drop existing table
    pg_cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
    
    # Build CREATE TABLE statement
    columns = []
    primary_keys = []
    
    for col in schema:
        col_id, name, col_type, notnull, default_value, is_pk = col
        
        # Convert type
        pg_type = sqlite_to_postgres_type(col_type)
        
        # Build column definition
        col_def = f"{name} {pg_type}"
        
        if is_pk:
            primary_keys.append(name)
        
        if notnull and not is_pk:
            col_def += " NOT NULL"
        
        if default_value is not None:
            # Handle default values
            if col_type.upper() == 'BOOLEAN':
                # Convert 0/1 to FALSE/TRUE
                col_def += f" DEFAULT {' TRUE' if str(default_value) == '1' else 'FALSE'}"
            elif col_type.upper() in ['TEXT', 'DATETIME']:
                if str(default_value).upper() not in ['NULL', 'CURRENT_TIMESTAMP']:
                    # Escape single quotes in the value
                    escaped_value = str(default_value).replace("'", "''")
                    col_def += f" DEFAULT '{escaped_value}'"
                elif str(default_value).upper() == 'CURRENT_TIMESTAMP':
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
            else:
                col_def += f" DEFAULT {default_value}"
        
        columns.append(col_def)
    
    # Add primary key constraint
    if primary_keys:
        columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
    
    create_query = f"CREATE TABLE {table_name} ({', '.join(columns)})"
    
    try:
        pg_cursor.execute(create_query)
        pg_conn.commit()
        print(f"   ✅ Created table {table_name}")
        return True
    except Exception as e:
        print(f"   ❌ Error creating table {table_name}: {e}")
        pg_conn.rollback()
        return False

def migrate_table_data(sqlite_conn, pg_conn, table_name):
    """Migrate data from SQLite table to PostgreSQL table"""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get all data
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"   ⚠️  No data to migrate from {table_name}")
        return 0
    
    # Get column names
    columns = [desc[0] for desc in sqlite_cursor.description]
    columns_str = ', '.join(columns)
    
    # Convert data
    data = []
    for row in rows:
        row_data = []
        for val in row:
            # Convert boolean 0/1 to True/False
            if isinstance(val, int) and val in [0, 1]:
                row_data.append(bool(val))
            else:
                row_data.append(val)
        data.append(tuple(row_data))
    
    # Insert data
    try:
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES %s"
        execute_values(pg_cursor, query, data, page_size=100)
        pg_conn.commit()
        print(f"   ✅ Migrated {len(data)} rows to {table_name}")
        return len(data)
    except Exception as e:
        print(f"   ❌ Error migrating data to {table_name}: {e}")
        pg_conn.rollback()
        return 0

def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   SQLite → PostgreSQL Auto-Migration                         ║")
    print("║   Mirrors exact schema + data                                ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Connect to SQLite
    print(f"📂 Connecting to SQLite: {SQLITE_DB_PATH}")
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"   ❌ Database not found!")
        return False
    
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    print("   ✅ SQLite connected")
    
    # Connect to PostgreSQL
    print(f"\n🐘 Connecting to PostgreSQL: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        pg_conn.autocommit = False
        print("   ✅ PostgreSQL connected")
    except Exception as e:
        print(f"   ❌ PostgreSQL connection failed: {e}")
        return False
    
    # Get all tables from SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    
    print(f"\n📋 Found {len(tables)} tables to migrate")
    print("=" * 70)
    
    total_rows = 0
    
    # Migrate each table
    for table_name in tables:
        print(f"\n📦 Migrating: {table_name}")
        print("-" * 70)
        
        # Create table
        if not create_postgres_table_from_sqlite(pg_conn, sqlite_conn, table_name):
            continue
        
        # Migrate data
        rows = migrate_table_data(sqlite_conn, pg_conn, table_name)
        total_rows += rows
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 70)
    print(f"✅ Migration Complete!")
    print(f"   Total rows migrated: {total_rows}")
    print("=" * 70)
    
    print("\n🚀 Next Steps:")
    print("   1. Update backend to use PostgreSQL")
    print("   2. Test all API endpoints")
    print("   3. Restart backend service")
    
    return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
