import sqlite3
c = sqlite3.connect(r'C:\backend\zwesta_trading.db').cursor()
c.execute("SELECT bot_id, name, enabled, status FROM user_bots ORDER BY created_at DESC")
for r in c.fetchall():
    print(r)
