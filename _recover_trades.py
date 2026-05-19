import sqlite3

src = r'C:\backend\zwesta_trading.db'
dst = r'C:\backend\zwesta_trading_clean.db'

src_conn = sqlite3.connect(src)
src_conn.row_factory = sqlite3.Row
dst_conn = sqlite3.connect(dst)
src_cur = src_conn.cursor()
dst_cur = dst_conn.cursor()

# Try to copy trades row by row, skipping bad ones
recovered = 0
failed = 0
try:
    src_cur.execute('SELECT * FROM trades')
    while True:
        try:
            row = src_cur.fetchone()
            if row is None:
                break
            cols = list(row.keys())
            placeholders = ','.join(['?' for _ in cols])
            col_names = ','.join(cols)
            try:
                dst_cur.execute(f'INSERT OR IGNORE INTO trades ({col_names}) VALUES ({placeholders})', [row[c] for c in cols])
                recovered += 1
            except Exception as e2:
                failed += 1
        except Exception as e:
            failed += 1
    dst_conn.commit()
except Exception as e:
    print('Outer error:', e)

print(f'Trades: {recovered} recovered, {failed} failed')
src_conn.close()
dst_conn.close()
