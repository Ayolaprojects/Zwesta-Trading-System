import os, sqlite3
path = r'C:\zwesta-trader\Zwesta Flutter App\zwesta_trading_test.db'
print('Inspecting DB at', path)
print('exists', os.path.exists(path))
conn = sqlite3.connect(path)
c = conn.cursor()
c.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
print('tables:')
for row in c.fetchall():
    print(row)
print('user_preferences:')
try:
    c.execute('SELECT * FROM user_preferences')
    for row in c.fetchall():
        print(row)
except Exception as e:
    print('user_preferences error', e)
print('broker_credentials:')
try:
    c.execute('SELECT * FROM broker_credentials')
    for row in c.fetchall():
        print(row)
except Exception as e:
    print('broker_credentials error', e)
conn.close()
