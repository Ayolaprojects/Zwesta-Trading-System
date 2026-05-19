import sqlite3, os, shutil
from datetime import datetime

src = r'C:\zwesta-trader\zwesta_trading.db'
dst = r'C:\backend\zwesta_trading_vps.db'

if not os.path.exists(src):
    print('NOT FOUND:', src)
    raise SystemExit(1)

conn = sqlite3.connect(src)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('PRAGMA integrity_check')
integrity = cur.fetchone()[0]
print('Source integrity:', integrity)

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', len(tables), tables)

for t in ['user_bots', 'users', 'broker_credentials', 'trades', 'user_sessions']:
    if t in tables:
        try:
            cur.execute('SELECT COUNT(*) FROM ' + t)
            print(t + ':', cur.fetchone()[0])
        except Exception as e:
            print(t + ': ERROR -', e)

conn.close()

if integrity != 'ok':
    print('DB is corrupted, cannot use as source.')
    raise SystemExit(1)

# Build clean VPS DB from this source (schema + data, bots cleared)
if os.path.exists(dst):
    os.remove(dst)

src_conn = sqlite3.connect(src)
src_conn.row_factory = sqlite3.Row
dst_conn = sqlite3.connect(dst)
src_cur = src_conn.cursor()
dst_cur = dst_conn.cursor()

src_cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
all_tables = src_cur.fetchall()

for t in all_tables:
    if t['sql'] and not t['name'].startswith('sqlite_'):
        try:
            dst_cur.execute(t['sql'])
        except Exception as e:
            print('Schema error:', t['name'], e)

dst_conn.execute('PRAGMA journal_mode=WAL')
dst_conn.commit()

SKIP = {'user_bots', 'user_sessions', 'bot_monitoring', 'worker_pool', 'worker_bot_queue', 'worker_bot_assignments'}

for t in all_tables:
    tname = t['name']
    if tname.startswith('sqlite_'):
        continue
    if tname in SKIP:
        print('CLEARED:', tname)
        continue
    try:
        src_cur.execute('SELECT * FROM ' + tname)
        rows = src_cur.fetchall()
        recovered = 0
        if rows:
            cols = list(rows[0].keys())
            placeholders = ','.join(['?' for _ in cols])
            col_names = ','.join(cols)
            for row in rows:
                try:
                    dst_cur.execute(
                        'INSERT OR IGNORE INTO ' + tname + ' (' + col_names + ') VALUES (' + placeholders + ')',
                        [row[c] for c in cols]
                    )
                    recovered += 1
                except Exception:
                    pass
        dst_conn.commit()
        print('Copied ' + tname + ': ' + str(recovered))
    except Exception as e:
        print('ERROR copying ' + tname + ': ' + str(e))

dst_cur.execute('PRAGMA integrity_check')
final = dst_cur.fetchone()[0]
print()
print('VPS DB integrity:', final)
src_conn.close()
dst_conn.close()

if final == 'ok':
    print('Ready to copy to VPS:')
    print('  ' + dst + ' -> C:\\backend\\zwesta_trading.db (on VPS)')
else:
    print('ERROR: integrity check failed')
