import sqlite3
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Check broker credentials
cursor.execute("SELECT credential_id, broker_name, account_number, is_live FROM broker_credentials WHERE user_id = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'")
credentials = cursor.fetchall()
print('Broker credentials for user:')
for cred in credentials:
    credential_id, broker_name, account_number, is_live = cred
    print(f'  {credential_id}: {broker_name} account {account_number} (live={is_live})')

# Check bot_credentials linking
cursor.execute("SELECT bot_id, credential_id FROM bot_credentials WHERE bot_id IN ('bot_1777234994531', 'bot_1777235140561_7dc40c1b', 'bot_1777238322914')")
bot_creds = cursor.fetchall()
print(f'\nBot to credential mapping:')
for bot_cred in bot_creds:
    bot_id, credential_id = bot_cred
    print(f'  {bot_id} -> {credential_id}')

conn.close()