import sqlite3
conn = sqlite3.connect('xm_trading_system/zwesta_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
mt5_tables = [t[0] for t in tables if 'mt5' in t[0].lower()]
print('MT5 tables:', mt5_tables)
for table in mt5_tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    count = cursor.fetchone()[0]
    print(f'{table}: {count} rows')
conn.close()