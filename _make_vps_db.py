import sqlite3, os, shutil
from datetime import datetime

src = r'C:\backend\zwesta_trading.db'
dst = r'C:\backend\zwesta_trading_vps.db'

if os.path.exists(dst):
    os.remove(dst)

src_conn = sqlite3.connect(src)
src_conn.row_factory = sqlite3.Row
dst_conn = sqlite3.connect(dst)
src_cur = src_conn.cursor()
dst_cur = dst_conn.cursor()

src_cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
tables = src_cur.fetchall()
for t in tables:
    if t['sql'] and not t['name'].startswith('sqlite_'):
        dst_cur.execute(t['sql'])

dst_conn.execute('PRAGMA journal_mode=WAL')
dst_conn.commit()

dst_cur.execute('PRAGMA integrity_check')
print('VPS DB integrity:', dst_cur.fetchone()[0])
dst_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables:', len(dst_cur.fetchall()))

src_conn.close()
dst_conn.close()
print('Created:', dst)
print()
print('Copy to VPS:')
print('  Local:  C:\\backend\\zwesta_trading_vps.db')
print('  -> VPS: C:\\backend\\zwesta_trading.db')
