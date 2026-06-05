import sqlite3
import os

db_paths = [
    'zwesta.db',
    'c:\\zwesta-trader\\zwesta.db',
    'c:\\backend\\zwesta.db',
    os.path.expanduser('~/zwesta.db'),
]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"✅ Found database: {db_path}\n")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables:")
        for t in tables:
            print(f"  - {t[0]}")
        conn.close()
        break
else:
    print("❌ Could not find database in any expected location")
    print("Checked:")
    for p in db_paths:
        print(f"  - {p}")
