"""
Quick script to check actual SQLite schema
"""
import sqlite3

db_path = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("📊 SQLite Database Schema Analysis\n")
print("=" * 70)

for table in tables:
    table_name = table[0]
    print(f"\n📋 Table: {table_name}")
    print("-" * 70)
    
    # Get table schema
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    for col in columns:
        col_id, name, type, notnull, default, pk = col
        pk_str = " PRIMARY KEY" if pk else ""
        notnull_str = " NOT NULL" if notnull else ""
        default_str = f" DEFAULT {default}" if default else ""
        print(f"  {name:<30} {type:<15}{pk_str}{notnull_str}{default_str}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n  📈 Rows: {count}")
    print("=" * 70)

conn.close()
