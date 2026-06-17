#!/usr/bin/env python3
import sqlite3

db = sqlite3.connect('zwesta_trading.db')
cursor = db.cursor()

# Get column names
cursor.execute("PRAGMA table_info(user_bots)")
columns = cursor.fetchall()

print("Column names in user_bots table:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n\nFirst bot data:")
cursor.execute("SELECT * FROM user_bots LIMIT 1")
bot = cursor.fetchone()
if bot:
    for i, col_info in enumerate(columns):
        col_name = col_info[1]
        print(f"  {col_name}: {bot[i]}")

db.close()
