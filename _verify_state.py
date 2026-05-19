import sqlite3, json
c = sqlite3.connect(r'C:\backend\zwesta_trading.db'); c.row_factory = sqlite3.Row
cur = c.cursor()
USER = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
print('--- BOTS ---')
for r in cur.execute("SELECT bot_id,name,strategy,broker_account_id,symbols,is_live,enabled FROM user_bots WHERE user_id=?", (USER,)).fetchall():
    print(f"  {r['bot_id']}  {r['name']:<22}  {r['broker_account_id']:<20}  live={r['is_live']}  enabled={r['enabled']}")
print('\n--- CREDS ---')
for r in cur.execute("SELECT credential_id,broker_name,account_number,server,is_live,password,api_key FROM broker_credentials WHERE user_id=?", (USER,)).fetchall():
    pw = r['password'] or ''
    ak = r['api_key'] or ''
    print(f"  {r['credential_id'][:8]}  {r['broker_name']:<10}  acct={r['account_number']}  server={r['server']}  pw_enc={pw.startswith('enc:v1:')}  ak_enc={ak.startswith('enc:v1:') if ak else 'no_key'}")
print('\n--- BINANCE OPT ---')
for r in cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Binance_%' AND user_id=?", (USER,)).fetchall():
    s = json.loads(r['runtime_state'])
    print(f"  {r['bot_id']} signalThreshold={s.get('signalThreshold')} mode={s.get('signalThresholdMode')} autoSwitch={s.get('autoSwitch')}")
