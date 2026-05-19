import sqlite3
con = sqlite3.connect(r'C:\backend\zwesta_trading.db')
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
for r in cur.fetchall():
    print(r[0])
