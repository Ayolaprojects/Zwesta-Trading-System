import sqlite3, json

db = r'C:\backend\zwesta_trading.db'
bot_id = 'bot_1778970971191'
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

row = c.execute('SELECT runtime_state FROM user_bots WHERE bot_id=?', (bot_id,)).fetchone()
state = json.loads(row['runtime_state'])

# Show before
pp = state.get('profitProtection', {})
print('BEFORE profitProtection:')
for k in ['breakEvenBufferProfit','retraceClosePercent','minLockedProfit','breakEvenActivationShare','peakProfitHardLockShare']:
    print(f'  {k}: {pp.get(k)}')

# Apply fixes
pp['breakEvenBufferProfit'] = 10.0      # was 0.5  - ensure real profit on each trade close
pp['retraceClosePercent'] = 10.0        # was 22.0 - tighter trailing stop
pp['minLockedProfit'] = 5.0             # was 0.0  - always lock $5 floor
pp['breakEvenActivationShare'] = 0.30  # was 0.5  - arm protection at 30% of peak not 50%
pp['peakProfitHardLockShare'] = 0.90   # was 0.95 - trigger hard lock at 90% drop from peak

state['profitProtection'] = pp

c.execute('UPDATE user_bots SET runtime_state=? WHERE bot_id=?', (json.dumps(state), bot_id))
conn.commit()
print('\nAFTER profitProtection:')
for k in ['breakEvenBufferProfit','retraceClosePercent','minLockedProfit','breakEvenActivationShare','peakProfitHardLockShare']:
    print(f'  {k}: {pp.get(k)}')

conn.close()
print('\nDB updated successfully.')
