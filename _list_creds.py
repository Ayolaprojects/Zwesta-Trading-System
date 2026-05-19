import sqlite3, json
db = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()
rows = c.execute('SELECT credential_id, broker_name, account_number, is_live, server, is_active FROM broker_credentials WHERE user_id=?', ('8e74db37-fd1e-4c57-87c4-ad3b64012ecf',)).fetchall()
print('All broker credentials:')
for r in rows:
    cid = r['credential_id'][:8]
    bn = r['broker_name']
    ac = r['account_number']
    il = r['is_live']
    sv = r['server']
    ia = r['is_active']
    print(f'  {cid}... {bn} | account={ac} | is_live={il} | server={sv} | active={ia}')
conn.close()
