#!/usr/bin/env python3
"""Check user_bots schema"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    database=os.getenv('DB_NAME', 'zwesta_trading'),
    user=os.getenv('DB_USER', 'zwesta_admin'),
    password=os.getenv('DB_PASSWORD', 'Zwesta@Trading2026!')
)
cursor = conn.cursor(cursor_factory=RealDictCursor)

# Get columns from user_bots table
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'user_bots'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()
print("Columns in user_bots table:")
print("=" * 60)
for col in columns:
    null_str = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
    print(f"  {col['column_name']:<30} {col['data_type']:<15} {null_str}")

# Sample data
print("\n\nSample bots:")
print("=" * 60)
cursor.execute("SELECT * FROM user_bots LIMIT 5")
sample = cursor.fetchall()
if sample:
    for bot in sample:
        print(f"  {bot}")

conn.close()
