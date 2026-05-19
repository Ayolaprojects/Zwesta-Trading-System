"""
Run this script DIRECTLY ON THE VPS (via RDP).
It patches bot_1778274193141 (Exness) config in the SQLite DB:
  - maxDailyLoss: 160 → 500   (room for ~6 trades instead of 2)
  - riskPerTrade: 30 → 3      (conservative position sizing)
  - tradeAmount:  869 → 600   (slightly smaller base)
  - managementProfile: fast_growth → balanced

After running this, restart the backend service.
The daily P/L will be auto-reset on restart, and the bot will
start with the new safer config.
"""

import sqlite3, json, os, glob, sys
from datetime import datetime

BOT_ID = 'bot_1778274193141'

# ── find the database ──────────────────────────────────────────────────────────
candidates = [
    r'C:\backend\zwesta_trading.db',
    r'C:\zwesta_trading.db',
    '/home/ubuntu/backend/zwesta_trading.db',
    '/root/backend/zwesta_trading.db',
    '/opt/backend/zwesta_trading.db',
    '/home/user/backend/zwesta_trading.db',
]
# also search common locations
for pattern in ['/home/*/backend/*.db', '/root/*.db', '/opt/*.db']:
    candidates += glob.glob(pattern)

db_path = None
for c in candidates:
    if os.path.exists(c):
        db_path = c
        break

if not db_path:
    print("ERROR: Could not find zwesta_trading.db")
    print("Please set db_path manually at the top of this script.")
    sys.exit(1)

print(f"Using DB: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# ── read current config ────────────────────────────────────────────────────────
row = conn.execute('SELECT * FROM user_bots WHERE bot_id = ?', (BOT_ID,)).fetchone()
if not row:
    print(f"ERROR: Bot {BOT_ID} not found in DB")
    conn.close()
    sys.exit(1)

print(f"\nFound bot: {BOT_ID}")

# PRAGMA table_info returns (cid, name, type, notnull, dflt_value, pk)
# d[1] gives the column name
pragma_rows = conn.execute('PRAGMA table_info(user_bots)').fetchall()
col_names = [d[1] for d in pragma_rows]   # name is field index 1
print(f"Columns: {col_names}")

# Find the JSON config column by name first
config_col = None
for col in ['config', 'settings', 'bot_config', 'runtime_state']:
    if col in col_names:
        config_col = col
        break

if config_col is None:
    # Fall back: scan all string columns for one that contains 'riskPerTrade'
    print("\nSearching for config column by content...")
    for idx, name in enumerate(col_names):
        try:
            val = row[idx]
            if val and isinstance(val, str) and 'riskPerTrade' in val:
                config_col = name
                print(f"  Found config in column '{name}' (index {idx})")
                break
            elif val and isinstance(val, str) and len(val) > 50:
                print(f"  {name}: {str(val)[:100]}")
        except Exception:
            pass

if config_col is None:
    print("\nERROR: Could not find config column.")
    conn.close()
    sys.exit(1)

print(f"Config column: {config_col}")
raw = row[col_names.index(config_col)]
cfg = json.loads(raw) if isinstance(raw, str) else {}

print(f"\nCurrent values:")
print(f"  maxDailyLoss     = {cfg.get('maxDailyLoss')}")
print(f"  riskPerTrade     = {cfg.get('riskPerTrade')}")
print(f"  tradeAmount      = {cfg.get('tradeAmount')}")
print(f"  managementProfile= {cfg.get('managementProfile')}")
print(f"  dailyProfit      = {cfg.get('dailyProfit')}")
print(f"  status           = {cfg.get('status')}")
print(f"  pauseReason      = {cfg.get('pauseReason')}")

# ── apply patches ──────────────────────────────────────────────────────────────
cfg['maxDailyLoss'] = 500.0
cfg['riskPerTrade'] = 3.0
cfg['tradeAmount'] = 600.0
cfg['managementProfile'] = 'balanced'
# Also clear the daily loss so it can trade again immediately on restart
today = datetime.now().strftime('%Y-%m-%d')
if isinstance(cfg.get('dailyProfits'), dict):
    cfg['dailyProfits'][today] = 0.0
cfg['dailyProfit'] = 0.0
if cfg.get('status') == 'PAUSED':
    cfg['status'] = 'ACTIVE'
pause = str(cfg.get('pauseReason') or '')
if 'Daily loss limit hit' in pause:
    cfg['pauseReason'] = None

updated = json.dumps(cfg)
# Use the actual column name found above
conn.execute(f'UPDATE user_bots SET "{config_col}" = ? WHERE bot_id = ?', (updated, BOT_ID))
conn.commit()

print(f"\nPatched values:")
print(f"  maxDailyLoss     = {cfg.get('maxDailyLoss')}")
print(f"  riskPerTrade     = {cfg.get('riskPerTrade')}")
print(f"  tradeAmount      = {cfg.get('tradeAmount')}")
print(f"  managementProfile= {cfg.get('managementProfile')}")
print(f"  dailyProfit      = {cfg.get('dailyProfit')}")
print(f"  pauseReason      = {cfg.get('pauseReason')}")

conn.close()
print("\n✅ DB patched. Now restart the backend service.")
print("   The Exness bot will start fresh with no daily loss count.")
