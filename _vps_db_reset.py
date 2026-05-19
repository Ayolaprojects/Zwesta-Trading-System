"""
VPS DB Reset Script - for severely corrupted databases where sqlite_master fails.
Run on VPS: python _vps_db_reset.py
"""
import os, shutil, sqlite3
from datetime import datetime

DB_PATH = r'C:\backend\zwesta_trading.db'
BAK_PATH = r'C:\backend\zwesta_trading.db.corrupt.' + datetime.now().strftime('%Y%m%d_%H%M%S')

print(f'[1] Moving corrupted DB to {BAK_PATH}')
shutil.move(DB_PATH, BAK_PATH)
print('    Done.')

print('[2] Creating fresh empty DB...')
conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA integrity_check')
conn.commit()
conn.close()
print('    Created:', DB_PATH)

print()
print('=== DONE ===')
print('The backend will recreate all tables on next startup.')
print('Run: python multi_broker_backend_updated.py')
print()
print('NOTE: All bot and trade data is gone (was unrecoverable).')
print(f'Corrupted backup kept at: {BAK_PATH}')
