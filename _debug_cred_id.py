import sqlite3
db = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db)
print('Searching for 22620ceb in broker_credentials:')
rows = conn.execute("SELECT credential_id, label, server FROM broker_credentials WHERE credential_id LIKE '%22620ceb%'").fetchall()
print('Found:', len(rows), rows)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
# Also check if there's a second db file
import os
for f in os.listdir(r'C:\backend'):
    if f.endswith('.db'):
        print('DB file:', f, os.path.getsize(r'C:\backend\\' + f))
conn.close()
