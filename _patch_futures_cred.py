import sqlite3
db = r'C:\backend\zwesta_trading.db'
cred_id = '5fe101ac-dcb5-4d3f-85f3-f4b23f03a31c'
conn = sqlite3.connect(db)
conn.execute("UPDATE broker_credentials SET cached_balance=10000, cached_margin_free=5000 WHERE credential_id=?", (cred_id,))
conn.commit()
r = conn.execute("SELECT credential_id, cached_balance, cached_margin_free FROM broker_credentials WHERE credential_id=?", (cred_id,)).fetchone()
print('Updated:', r)
conn.close()
