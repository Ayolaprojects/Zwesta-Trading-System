import sqlite3, json
from datetime import datetime, timezone, timedelta

db = r"C:\backend\zwesta_trading.db"
conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# List all tables
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in c.fetchall()]
print("TABLES:", tables)

BOT_IDS = ['bot_1778971251604', 'bot_1778970971191']
TODAY = '2026-05-17'

# ── 1. Find bots in any table ─────────────────────────────────────────────────
print("\n=== BOT CONFIG RAW ===")
for tbl in tables:
    try:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({tbl})")]
        if 'bot_id' not in cols:
            continue
        for bot_id in BOT_IDS:
            c.execute(f"SELECT * FROM {tbl} WHERE bot_id=? LIMIT 1", (bot_id,))
            row = c.fetchone()
            if row:
                d = dict(row)
                # parse JSON blobs
                for k in ('config','state','data','bot_config','settings'):
                    if k in d and d[k]:
                        try:
                            d[k] = json.loads(d[k])
                        except Exception:
                            pass
                print(f"\n  [{tbl}] {bot_id}")
                cfg = d.get('config') or d.get('bot_config') or d.get('settings') or {}
                if isinstance(cfg, dict):
                    interesting = ['enabled','mode','broker','symbol','managementProfile',
                                   'accountBalance','accountEquity','tradeAmount','riskPerTrade',
                                   'maxDailyLoss','maxOpenPositions','allowedVolatility',
                                   'effectiveAllowedVolatility','signalThreshold','effectiveSignalThreshold',
                                   'winRate','totalTrades','totalProfit','todayPnl','openPositionCount',
                                   'tradeHistoryCount','consecutiveLosses']
                    for k in interesting:
                        if k in cfg:
                            print(f"    {k}: {cfg[k]}")
                # top-level non-blob fields
                for k,v in d.items():
                    if k not in ('config','state','data','bot_config','settings') and v is not None:
                        print(f"    [col] {k}: {v}")
    except Exception as e:
        print(f"  Error on {tbl}: {e}")

# ── 2. Trade history for each bot ─────────────────────────────────────────────
print("\n\n=== TRADE COUNTS & P/L FROM DB ===")
for tbl in tables:
    try:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({tbl})")]
        if 'bot_id' not in cols:
            continue
        for bot_id in BOT_IDS:
            c.execute(f"SELECT COUNT(*) FROM {tbl} WHERE bot_id=?", (bot_id,))
            cnt = c.fetchone()[0]
            if cnt > 0:
                print(f"\n  [{tbl}] {bot_id}: {cnt} rows")
                # check if there's profit column
                if 'profit' in cols:
                    c.execute(f"SELECT COUNT(*), SUM(profit), SUM(CASE WHEN profit>0 THEN 1 ELSE 0 END) FROM {tbl} WHERE bot_id=?", (bot_id,))
                    row = c.fetchone()
                    print(f"    total trades={row[0]}, sum_profit={row[1]:.4f}, wins={row[2]}")
                    win_rate = (row[2] / row[0] * 100) if row[0] else 0
                    print(f"    win_rate={win_rate:.1f}%")
                    # today
                    if any('open_time' in col or 'close_time' in col or 'timestamp' in col for col in cols):
                        time_col = next((col for col in cols if 'close' in col or 'time' in col), None)
                        if time_col:
                            c.execute(f"SELECT COUNT(*), SUM(profit) FROM {tbl} WHERE bot_id=? AND {time_col} LIKE ?", (bot_id, f'{TODAY}%'))
                            row2 = c.fetchone()
                            print(f"    today ({TODAY}): trades={row2[0]}, pnl={row2[1]}")
                    # last 5 trades
                    time_col2 = next((col for col in cols if 'close' in col or 'time' in col or 'stamp' in col), None)
                    order = f"ORDER BY {time_col2} DESC" if time_col2 else ""
                    c.execute(f"SELECT * FROM {tbl} WHERE bot_id=? {order} LIMIT 5", (bot_id,))
                    rows = c.fetchall()
                    print(f"    last 5 trades:")
                    for r in rows:
                        rd = dict(r)
                        print(f"      {rd.get('symbol','?')} {rd.get('direction',rd.get('side','?'))} profit={rd.get('profit','?')} close={rd.get('close_time',rd.get('timestamp','?'))}")
    except Exception as e:
        print(f"  Error on {tbl}: {e}")

# ── 3. Recent trades across all bots (dashboard view) ─────────────────────────
print("\n\n=== RECENT TRADES (ALL BOTS TODAY) ===")
for tbl in tables:
    try:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({tbl})")]
        if 'profit' not in cols:
            continue
        time_col = next((col for col in cols if 'close' in col), None)
        if not time_col:
            time_col = next((col for col in cols if 'time' in col or 'stamp' in col), None)
        if not time_col:
            continue
        c.execute(f"SELECT bot_id, symbol, profit, {time_col} FROM {tbl} WHERE {time_col} LIKE ? ORDER BY {time_col} DESC LIMIT 10", (f'{TODAY}%',))
        rows = c.fetchall()
        if rows:
            print(f"\n  [{tbl}] recent trades today:")
            for r in rows:
                print(f"    bot={r[0]} sym={r[1]} profit={r[2]} time={r[3]}")
    except Exception as e:
        pass

# ── 4. Account balance check ──────────────────────────────────────────────────
print("\n\n=== BALANCE CHECK ===")
for tbl in tables:
    try:
        cols = [row[1] for row in conn.execute(f"PRAGMA table_info({tbl})")]
        if 'balance' in cols or 'account_balance' in cols:
            bal_col = 'balance' if 'balance' in cols else 'account_balance'
            c.execute(f"SELECT bot_id, {bal_col} FROM {tbl} LIMIT 20")
            for r in c.fetchall():
                if r[1]:
                    print(f"  [{tbl}] bot={r[0]} balance={r[1]}")
    except Exception:
        pass

conn.close()
print("\nDone.")
