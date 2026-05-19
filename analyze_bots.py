#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('Zwesta Flutter App/zwesta_trading.db')
cursor = conn.cursor()

print('🔍 DATABASE SCHEMA ANALYSIS')
print('='*50)

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('📋 Tables:', [t[0] for t in tables])

# Check user_bots table structure
print('\n🤖 USER_BOTS TABLE:')
cursor.execute('PRAGMA table_info(user_bots)')
columns = cursor.fetchall()
for col in columns:
    print(f'   {col[1]} ({col[2]})')

# Check recent bots
print('\n📊 RECENT BOTS:')
cursor.execute('SELECT bot_id, name, strategy, status, enabled FROM user_bots ORDER BY created_at DESC LIMIT 3')
bots = cursor.fetchall()
for bot in bots:
    print(f'   Bot: {bot}')

# Check market signals
print('\n📊 RECENT MARKET SIGNALS:')
try:
    cursor.execute('SELECT symbol, signal_strength, timestamp FROM market_signals ORDER BY timestamp DESC LIMIT 5')
    signals = cursor.fetchall()
    if signals:
        for symbol, strength, timestamp in signals:
            print(f'   {symbol}: {strength}/100 at {timestamp}')
    else:
        print('   No signals found')
except sqlite3.OperationalError:
    print('   market_signals table does not exist')

# Check trades
print('\n💰 RECENT TRADES:')
cursor.execute('PRAGMA table_info(trades)')
trade_columns = cursor.fetchall()
print('   Trade table columns:', [col[1] for col in trade_columns])

cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT 3')
trades = cursor.fetchall()
if trades:
    for trade in trades:
        print(f'   Trade: {trade}')
else:
    print('   No trades found')

conn.close()