"""
Directly patch bot states in the SQLite database.
Sets managementMode=manual, allowedVolatility=['Low','Medium','High'] for both Binance bots.
"""
import sqlite3, json
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'

BINANCE_BOTS = ['bot_1778970971191', 'bot_1778971251604']

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute('PRAGMA busy_timeout = 5000')
cur = conn.cursor()

# First check what's in the DB
cur.execute('SELECT bot_id, bot_state FROM user_bots WHERE bot_id IN (?,?)', tuple(BINANCE_BOTS))
rows = cur.fetchall()

if not rows:
    print('ERROR: Bots not found in this database. This is not the live VPS DB.')
    conn.close()
    exit(1)

print(f'Found {len(rows)} bots in DB.')
for row in rows:
    state = json.loads(row['bot_state'] or '{}')
    print(f"  {row['bot_id']}: allowedVolatility={state.get('allowedVolatility')}, managementMode={state.get('managementMode')}, enabled={state.get('enabled')}")

print()

# Patch each bot
for bot_id in BINANCE_BOTS:
    cur.execute('SELECT bot_state FROM user_bots WHERE bot_id = ?', (bot_id,))
    row = cur.fetchone()
    if not row:
        print(f'  WARNING: {bot_id} not found, skipping.')
        continue
    
    state = json.loads(row['bot_state'] or '{}')
    
    # Apply the fix
    state['managementMode'] = 'manual'
    state['signalThresholdMode'] = 'manual'
    state['allowedVolatility'] = ['Low', 'Medium', 'High']
    state['effectiveAllowedVolatility'] = ['Low', 'Medium', 'High']
    state['managementState'] = 'normal'
    
    new_state = json.dumps(state)
    cur.execute('UPDATE user_bots SET bot_state = ?, updated_at = ? WHERE bot_id = ?',
                (new_state, datetime.now().isoformat(), bot_id))
    print(f'  Patched {bot_id}')

conn.commit()
conn.close()

print('\nVerifying...')
conn2 = sqlite3.connect(DB)
conn2.row_factory = sqlite3.Row
cur2 = conn2.cursor()
cur2.execute('SELECT bot_id, bot_state FROM user_bots WHERE bot_id IN (?,?)', tuple(BINANCE_BOTS))
for row in cur2.fetchall():
    state = json.loads(row['bot_state'] or '{}')
    print(f"  {row['bot_id']}: allowedVolatility={state.get('allowedVolatility')}, managementMode={state.get('managementMode')}")
conn2.close()
print('Done.')
