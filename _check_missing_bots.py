"""
_check_missing_bots.py
Run this script to find any bot IDs that the Flutter app thinks exist
but are not registered in the backend Postgres database.
Usage: python _check_missing_bots.py
"""
import psycopg2, sqlite3, os, glob

PG = dict(host='localhost', dbname='zwesta_trading', user='zwesta_admin',
          password='Zwesta@Trading2026!', port=5432)

# --- Collect all bot_ids from Postgres ---
pg_conn = psycopg2.connect(**PG)
pg_cur = pg_conn.cursor()
pg_cur.execute("SELECT bot_id, name, status, enabled, is_live, broker_account_id FROM user_bots ORDER BY created_at DESC")
pg_rows = pg_cur.fetchall()
pg_ids = {r[0] for r in pg_rows}
pg_conn.close()

print(f"Postgres bots ({len(pg_ids)}):")
for r in pg_rows:
    print(f"  {r[0]}  enabled={r[3]}  live={r[4]}  acct={r[5]}")

# --- Collect all bot_ids from SQLite DBs ---
sqlite_dbs = (
    glob.glob(r'C:\zwesta-trader\**\*.db', recursive=True)
    + [r'C:\backend\zwesta_trading.db']
)
sqlite_ids = {}
for db_path in set(sqlite_dbs):
    if not os.path.exists(db_path):
        continue
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT bot_id FROM user_bots")
        for (bid,) in cur.fetchall():
            sqlite_ids.setdefault(bid, db_path)
        conn.close()
    except Exception:
        pass

# --- Find bots in SQLite not in Postgres ---
missing = {bid: src for bid, src in sqlite_ids.items() if bid not in pg_ids}

print(f"\nSQLite-only bots missing from Postgres ({len(missing)}):")
if missing:
    for bid, src in missing.items():
        print(f"  MISSING: {bid}  (from {src})")
    print("\nRun _create_two_binance_bots.py pattern to add them manually.")
else:
    print("  None — all SQLite bots are present in Postgres. ✅")
