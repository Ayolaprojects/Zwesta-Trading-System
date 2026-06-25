import sqlite3
from datetime import datetime

conn = sqlite3.connect(r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading.db')
cur = conn.cursor()

# Get Exness credential_id
cur.execute("SELECT credential_id FROM broker_credentials WHERE broker_name LIKE '%Exness%'")
cred = cur.fetchone()
if cred:
    credential_id = cred[0]
    
    # Get the new Exness bot_id
    cur.execute("SELECT bot_id, user_id FROM user_bots WHERE symbols LIKE '%EURUSDm%'")
    bot = cur.fetchone()
    if bot:
        bot_id = bot[0]
        user_id = bot[1]
        
        cur.execute('INSERT OR REPLACE INTO bot_credentials (bot_id, credential_id, user_id, created_at) VALUES (?, ?, ?, ?)',
                    (bot_id, credential_id, user_id, datetime.now().isoformat()))
        conn.commit()
        print(f'Linked bot {bot_id} to credential {credential_id}')
    else:
        print('No Exness bot found')
else:
    print('No Exness credential found')

conn.close()