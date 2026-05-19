"""
VPS DB Recovery Script
Run this on the VPS: python _vps_db_recover.py
It will backup the corrupted DB, salvage what it can, and create a clean DB.
"""
import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = r'C:\backend\zwesta_trading.db'
CLEAN_PATH = r'C:\backend\zwesta_trading_clean.db'
BAK_PATH = r'C:\backend\zwesta_trading.db.bak.' + datetime.now().strftime('%Y%m%d_%H%M%S')

print(f'[1] Backing up {DB_PATH} -> {BAK_PATH}')
shutil.copy2(DB_PATH, BAK_PATH)
print(f'    Done.')

# Remove old clean DB if exists
if os.path.exists(CLEAN_PATH):
    os.remove(CLEAN_PATH)

src_conn = sqlite3.connect(DB_PATH)
src_conn.row_factory = sqlite3.Row
dst_conn = sqlite3.connect(CLEAN_PATH)
src_cur = src_conn.cursor()
dst_cur = dst_conn.cursor()

print('[2] Reading table schemas...')
src_cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
tables = src_cur.fetchall()
print(f'    Found {len(tables)} tables: {[t["name"] for t in tables]}')

print('[3] Creating clean DB schema...')
for t in tables:
    if t['sql'] and not t['name'].startswith('sqlite_'):
        try:
            dst_cur.execute(t['sql'])
            print(f'    Created: {t["name"]}')
        except Exception as e:
            print(f'    Schema error for {t["name"]}: {e}')
dst_conn.commit()

print('[4] Copying data table by table...')
skip_tables = {'user_bots'}  # wipe bots as they caused the issues
totals = {}

for t in tables:
    tname = t['name']
    if tname.startswith('sqlite_'):
        continue
    if tname in skip_tables:
        print(f'    SKIPPED: {tname} (intentionally cleared)')
        totals[tname] = 0
        continue
    try:
        src_cur.execute(f'SELECT * FROM {tname}')
        rows = src_cur.fetchall()
        recovered = 0
        failed = 0
        if rows:
            cols = list(rows[0].keys())
            placeholders = ','.join(['?' for _ in cols])
            col_names = ','.join(cols)
            for row in rows:
                try:
                    dst_cur.execute(
                        f'INSERT OR IGNORE INTO {tname} ({col_names}) VALUES ({placeholders})',
                        [row[c] for c in cols]
                    )
                    recovered += 1
                except Exception:
                    failed += 1
        dst_conn.commit()
        totals[tname] = recovered
        status = f'{recovered} rows' + (f' ({failed} failed)' if failed else '')
        print(f'    {tname}: {status}')
    except Exception as e:
        print(f'    ERROR copying {tname}: {e}')
        totals[tname] = 0

print('[5] Verifying clean DB integrity...')
check_cur = dst_conn.cursor()
check_cur.execute('PRAGMA integrity_check')
result = check_cur.fetchone()[0]
print(f'    Integrity: {result}')

src_conn.close()
dst_conn.close()

if result == 'ok':
    print('[6] Swapping clean DB into place...')
    os.replace(CLEAN_PATH, DB_PATH)
    print(f'    Done. {DB_PATH} is now clean.')
    print()
    print('=== SUMMARY ===')
    for tname, count in totals.items():
        print(f'  {tname}: {count}')
    print()
    print('Now restart the backend:')
    print('  Restart-Service ZwestaBackendAutoStart')
    print('  -- or --')
    print('  python multi_broker_backend_updated.py')
else:
    print(f'[!] Integrity check failed: {result}')
    print('    Clean DB NOT swapped in. Check manually.')
    os.remove(CLEAN_PATH)
