import sqlite3, json, sys
DB = r'C:\backend\zwesta_trading.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find candidate tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [r['name'] for r in cur.fetchall()]
candidates = [t for t in all_tables if 'trade' in t.lower() or 'order' in t.lower() or 'position' in t.lower()]
print("Candidate tables:", candidates)
print()

# For each candidate, get column list and BTC-related rows from May 5 16:00-17:00
for t in candidates:
    try:
        cur.execute(f"PRAGMA table_info({t})")
        cols = [c['name'] for c in cur.fetchall()]
        if not any(c in cols for c in ('symbol','pair','instrument')):
            continue
        sym_col = next((c for c in ('symbol','pair','instrument') if c in cols), None)
        time_cols = [c for c in cols if 'time' in c.lower() or 'date' in c.lower() or c in ('created_at','updated_at','closed_at','opened_at')]
        print(f"--- {t} (cols={len(cols)}) sym={sym_col} time_cols={time_cols}")
        cur.execute(f"SELECT * FROM {t} WHERE UPPER({sym_col}) LIKE '%BTC%' ORDER BY rowid DESC LIMIT 6")
        rows = cur.fetchall()
        for r in rows:
            d = dict(r)
            keep = {k: v for k, v in d.items() if k in ('id','trade_id','order_id','bot_id','symbol','pair','side','direction','action','quantity','volume','size','amount','entry_price','exit_price','price','open_price','close_price','status','pnl','profit','created_at','updated_at','closed_at','opened_at','timestamp','open_time','close_time','source')}
            print(json.dumps(keep, default=str))
        print()
    except Exception as e:
        print(f"  err on {t}: {e}")
