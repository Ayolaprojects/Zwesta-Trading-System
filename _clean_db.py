import sqlite3, os, shutil
SRC = r'C:\backend\zwesta_trading.db'
CLEAN = r'C:\backend\zwesta_trading_clean.db'
if os.path.exists(CLEAN):
    os.remove(CLEAN)
src = sqlite3.connect(SRC)
src.execute(f"VACUUM INTO '{CLEAN}'")
src.close()
chk = sqlite3.connect(CLEAN)
print('clean integrity:', chk.execute('PRAGMA integrity_check').fetchone())
print('users:', chk.execute('SELECT COUNT(*) FROM users').fetchone())
print('bots:', chk.execute('SELECT COUNT(*) FROM user_bots').fetchone())
print('creds:', chk.execute('SELECT COUNT(*) FROM broker_credentials').fetchone())
print('trades:', chk.execute('SELECT COUNT(*) FROM trades').fetchone())
chk.close()
print('clean db size:', os.path.getsize(CLEAN))
