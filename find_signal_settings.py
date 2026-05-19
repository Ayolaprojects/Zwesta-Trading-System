#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('Zwesta Flutter App/zwesta_trading.db')
cursor = conn.cursor()

print('🔍 CHECKING WHERE SIGNAL THRESHOLDS ARE STORED')
print('='*50)

# Check user_trading_settings table
print('\n📊 USER_TRADING_SETTINGS TABLE:')
cursor.execute('PRAGMA table_info(user_trading_settings)')
columns = cursor.fetchall()
for col in columns:
    print(f'   {col[1]} ({col[2]})')

# Check user_risk_settings table
print('\n📊 USER_RISK_SETTINGS TABLE:')
cursor.execute('PRAGMA table_info(user_risk_settings)')
columns = cursor.fetchall()
for col in columns:
    print(f'   {col[1]} ({col[2]})')

# Check if there are any signal-related settings
print('\n🔍 SEARCHING FOR SIGNAL SETTINGS:')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table_name, in tables:
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        signal_cols = [col[1] for col in columns if 'signal' in col[1].lower() or 'threshold' in col[1].lower()]
        if signal_cols:
            print(f'   {table_name}: {signal_cols}')
    except:
        pass

conn.close()