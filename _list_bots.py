import sqlite3, json
conn = sqlite3.connect(r'C:\backend\zwesta_trading.db')
c = conn.cursor()
c.execute("SELECT bot_id, name FROM user_bots")
rows = c.fetchall()
print("All bots:")
for r in rows:
    print(" ", r)
conn.close()
