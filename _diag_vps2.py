import sqlite3

conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== WORKER POOL ===")
c.execute("SELECT worker_id, pid, status, bot_count, heartbeat_at, error_message FROM worker_pool ORDER BY worker_id")
for row in c.fetchall():
    print(f"  worker_{row['worker_id']}: pid={row['pid']} status={row['status']} bots={row['bot_count']} heartbeat={row['heartbeat_at']}")

print("\n=== USER SESSIONS (last 3) ===")
c.execute("PRAGMA table_info(user_sessions)")
cols = [col[1] for col in c.fetchall()]
print(f"  Columns: {cols}")
c.execute("SELECT * FROM user_sessions ORDER BY rowid DESC LIMIT 3")
for row in c.fetchall():
    d = dict(row)
    # Show token + user_id only
    token = d.get('token') or d.get('access_token') or d.get('session_token') or 'N/A'
    uid = d.get('user_id', 'N/A')
    exp = d.get('expires_at') or d.get('expiry') or 'N/A'
    print(f"  user={uid} token={token[:20]}... exp={exp}")

print("\n=== USERS ===")
c.execute("SELECT user_id, username, email FROM users LIMIT 5")
for row in c.fetchall():
    print(f"  {row['user_id']}: {row['username']} / {row['email']}")

conn.close()
