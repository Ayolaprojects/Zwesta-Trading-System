import sqlite3, json

conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT bot_id, name, status, enabled, broker_account_id, daily_profit, total_profit, runtime_state FROM user_bots")
for row in c.fetchall():
    rt = json.loads(row['runtime_state'] or '{}')
    mp = rt.get('maxOpenPositions', 'N/A')
    paused = rt.get('drawdownPauseUntil', '')
    dl = rt.get('maxDailyLoss', rt.get('dailyLossLimit', ''))
    open_pos = rt.get('openPositions', {})
    n_open = len(open_pos) if isinstance(open_pos, dict) else 0
    print(row['bot_id'])
    print(f"  name={row['name']} status={row['status']} enabled={row['enabled']}")
    print(f"  account={row['broker_account_id']} daily_pnl={row['daily_profit']} total={row['total_profit']}")
    print(f"  maxOpenPositions={mp} openPositions={n_open} pauseUntil={paused} maxDailyLoss={dl}")
    print()

# Credentials
print("=== CREDENTIALS ===")
c.execute("SELECT credential_id, broker_name, account_number, is_active, is_live, last_update FROM broker_credentials")
for row in c.fetchall():
    print(f"  {row['credential_id']}: {row['broker_name']} acct={row['account_number']} is_active={row['is_active']} is_live={row['is_live']} last_update={row['last_update']}")

# Worker queue
print("\n=== PENDING WORKER QUEUE ===")
c.execute("SELECT id, bot_id, worker_id, command, status, created_at FROM worker_bot_queue WHERE status='pending' ORDER BY created_at DESC LIMIT 10")
rows = c.fetchall()
if not rows:
    print("  (empty)")
for row in rows:
    print(f"  id={row['id']} bot={row['bot_id']} worker={row['worker_id']} cmd={row['command']}")

# Worker pool
print("\n=== WORKER POOL ===")
c.execute("SELECT worker_id, status, pid, last_heartbeat FROM worker_pool ORDER BY worker_id")
for row in c.fetchall():
    print(f"  worker_{row['worker_id']}: status={row['status']} pid={row['pid']} heartbeat={row['last_heartbeat']}")

# Recent trades
print("\n=== RECENT TRADES (last 5) ===")
c.execute("SELECT trade_id, bot_id, symbol, status, profit, created_at FROM trades ORDER BY created_at DESC LIMIT 5")
for row in c.fetchall():
    print(f"  {row['trade_id']}: {row['symbol']} {row['status']} profit={row['profit']} at={row['created_at']}")

conn.close()
