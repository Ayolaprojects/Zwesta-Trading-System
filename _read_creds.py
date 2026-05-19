"""
Read broker_credentials and check actual Binance demo account state.
"""
import sqlite3, json

db = r'C:\backend\zwesta_trading.db'
cred_id = 'e568ec38-cfc7-4b05-8033-b56ecdf304e4'

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

row = c.execute(
    'SELECT credential_id, broker_name, account_number, is_live, api_key, password, server, cached_balance, cached_margin_free FROM broker_credentials WHERE credential_id=?',
    (cred_id,)
).fetchone()

if row:
    d = dict(row)
    print('broker_name:', d['broker_name'])
    print('account_number:', d['account_number'])
    print('is_live:', d['is_live'])
    print('server:', d['server'])
    print('cached_balance:', d['cached_balance'])
    print('cached_margin_free:', d['cached_margin_free'])
    print('api_key:', d['api_key'][:8] + '...' if d['api_key'] else 'None')
    print('api_secret length:', len(d['password']) if d['password'] else 0)
else:
    print('Credential not found')

conn.close()
