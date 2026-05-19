import sqlite3, json, os

src = r'C:\backend\zwesta_trading.db'
dst = r'C:\backend\zwesta_trading_recovered.db'

if os.path.exists(dst):
    os.remove(dst)

src_conn = sqlite3.connect(src)
dst_conn = sqlite3.connect(dst)

# Read all tables from corrupt source
tables = src_conn.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()
print(f'Tables: {[t[0] for t in tables]}')

for table_name, create_sql in tables:
    if not create_sql:
        continue
    try:
        dst_conn.execute(create_sql)
        dst_conn.commit()
        rows = src_conn.execute(f'SELECT * FROM {table_name}').fetchall()
        cols = [d[0] for d in src_conn.execute(f'SELECT * FROM {table_name} LIMIT 0').description]
        placeholders = ','.join(['?'] * len(cols))
        dst_conn.executemany(f'INSERT OR IGNORE INTO {table_name} VALUES ({placeholders})', rows)
        dst_conn.commit()
        print(f'{table_name}: copied {len(rows)} rows')
    except Exception as e:
        print(f'{table_name}: ERROR {e}')

src_conn.close()

# Now patch the bot in the recovered DB
bot_id = 'bot_1778970971191'
try:
    row = dst_conn.execute('SELECT runtime_state FROM user_bots WHERE bot_id=?', (bot_id,)).fetchone()
    if row:
        state = json.loads(row[0])
        state['effectivePositionSizeMultiplier'] = 1.0
        state['effectiveScannerCapitalMultiplier'] = 1.0
        state['effectiveTradeAmount'] = 3500.0
        state['riskPerTrade'] = 230.0
        state['maxDailyLoss'] = 920.0
        if isinstance(state.get('tradeAmountAdaptation'), dict):
            adapt = state['tradeAmountAdaptation']
            adapt['state'] = 'normal'
            adapt['multiplier'] = 1.0
            adapt['adjustedTradeAmount'] = 3500.0
            adapt['scannerCapitalMultiplier'] = 1.0
            adapt['retraceRatio'] = 0.0
        dst_conn.execute('UPDATE user_bots SET runtime_state=? WHERE bot_id=?', (json.dumps(state), bot_id))
        dst_conn.commit()
        print(f'\nPatched bot {bot_id} in recovered DB:')
        print(f'  effectiveTradeAmount = {state["effectiveTradeAmount"]}')
        print(f'  riskPerTrade = {state["riskPerTrade"]}')
    else:
        print('Bot not found in recovered DB')
except Exception as e:
    print(f'Patch error: {e}')

dst_conn.close()
print('\nRecovered DB saved to:', dst)
