import sqlite3
from runtime_infrastructure import get_database_path

path = get_database_path()
print('DBPATH:', path)
conn = sqlite3.connect(path)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print('TABLES:')
for row in cur.fetchall():
    print(' ', row[0])
conn.close()
