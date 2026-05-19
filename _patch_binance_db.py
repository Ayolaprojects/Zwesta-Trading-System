"""
Directly patch Binance bots in local SQLite DB:
- managementMode: manual
- signalThresholdMode: manual  
- allowedVolatility: ['Low', 'Medium', 'High']

This script auto-discovers the config column name.
Run on VPS: python _patch_binance_db.py
"""
import sqlite3, json, os, sys
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
if not os.path.exists(DB):
    print('ERROR: DB not found at', DB)
    sys.exit(1)

BINANCE_BOTS = ['bot_1778970971191', 'bot_1778971251604']

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute('PRAGMA busy_timeout = 5000')

# Find config column
pragma = conn.execute('PRAGMA table_info(user_bots)').fetchall()
col_names = [r[1] for r in pragma]
print('Columns:', col_names)

config_col = None
for col in ['config', 'settings', 'bot_config', 'runtime_state', 'bot_state']:
    if col in col_names:
        config_col = col
        break

if config_col is None:
    # Search by content
    row = conn.execute('SELECT * FROM user_bots LIMIT 1').fetchone()
    if row:
        for i, name in enumerate(col_names):
            try:
                val = row[i]
                if val and isinstance(val, str) and 'managementProfile' in val:
                    config_col = name
                    break
            except Exception:
                pass

print('Config column:', config_col)
if not config_col:
    print('ERROR: could not find config column')
    sys.exit(1)

# Check if target bots exist
rows = conn.execute(f'SELECT bot_id, {config_col} FROM user_bots WHERE bot_id IN (?,?)', 
                    tuple(BINANCE_BOTS)).fetchall()
print(f'Found {len(rows)} target bots')

if not rows:
    print('ERROR: Target bots not found in this DB. This is not the live VPS database.')
    conn.close()
    sys.exit(1)

for row in rows:
    bot_id = row[0]
    raw = row[1]
    cfg = json.loads(raw or '{}')
    print(f'\n{bot_id}: managementProfile={cfg.get("managementProfile")}, allowedVolatility={cfg.get("allowedVolatility")}')
    
    cfg['managementMode'] = 'manual'
    cfg['signalThresholdMode'] = 'manual'
    cfg['allowedVolatility'] = ['Low', 'Medium', 'High']
    cfg['effectiveAllowedVolatility'] = ['Low', 'Medium', 'High']
    cfg['managementState'] = 'normal'
    
    conn.execute(f'UPDATE user_bots SET "{config_col}" = ?, updated_at = ? WHERE bot_id = ?',
                 (json.dumps(cfg), datetime.now().isoformat(), bot_id))
    print(f'  -> Patched.')

conn.commit()
conn.close()
print('\nDone. Restart the backend for changes to take effect.')
