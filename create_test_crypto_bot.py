import sqlite3
import json
import uuid
from datetime import datetime

conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()

# Get test user ID
cursor.execute('SELECT user_id FROM users WHERE email = ?', ('test@example.com',))
user_result = cursor.fetchone()
if not user_result:
    print('❌ Test user not found')
    exit(1)

test_user_id = user_result[0]
print(f'📋 Using test user: {test_user_id}')

# Get a broker account for this user
cursor.execute('SELECT credential_id FROM broker_credentials WHERE user_id = ? LIMIT 1', (test_user_id,))
broker_result = cursor.fetchone()
if not broker_result:
    print('❌ No broker credentials found for test user')
    exit(1)

broker_account_id = broker_result[0]
print(f'📋 Using broker account: {broker_account_id}')

# Create a test bot with crypto symbols
bot_id = str(uuid.uuid4())
bot_name = 'Test Crypto Bot'
created_at = datetime.now().isoformat()

# Symbols as JSON string
symbols_json = json.dumps(['BTCUSD', 'ETHUSD'])

cursor.execute('''
INSERT INTO user_bots (bot_id, user_id, name, strategy, status, enabled, broker_account_id, symbols, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    bot_id,
    test_user_id,
    bot_name,
    'scalping',
    'active',
    1,
    broker_account_id,
    symbols_json,
    created_at,
    created_at
))

conn.commit()

print(f'✅ Created test crypto bot:')
print(f'   Bot ID: {bot_id}')
print(f'   Name: {bot_name}')
print(f'   Symbols: BTCUSD, ETHUSD')
print(f'   Crypto override threshold: 5 (should apply)')

# Verify the bot was created
cursor.execute('SELECT bot_id, name, symbols FROM user_bots WHERE bot_id = ?', (bot_id,))
bot = cursor.fetchone()
if bot:
    symbols = json.loads(bot[2])
    print(f'\n🔍 VERIFICATION:')
    print(f'   Bot exists: ✅')
    print(f'   Stored symbols: {symbols}')

conn.close()