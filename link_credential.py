import sqlite3

conn = sqlite3.connect(r'zwesta_trading.db')
cur = conn.cursor()

# Get the credential_id from the working bot
cur.execute("SELECT credential_id FROM bot_credentials WHERE bot_id = 'bot_1782256390089'")
row = cur.fetchone()
if row:
    credential_id = row[0]
    print(f'Found credential_id: {credential_id}')
    
    # Link the same credential to the new bot
    cur.execute("INSERT OR REPLACE INTO bot_credentials (bot_id, credential_id) VALUES (?, ?)", 
                ('bot_1782305458924', credential_id))
    conn.commit()
    print('Linked credential to bot_1782305458924')
else:
    print('No credential found on working bot')

conn.close()