import sqlite3, requests, json, time
from datetime import datetime, timezone

BASE = 'http://148.113.5.39:9000'
KEY = 'zwesta_live_api_key_2026_secure'
ADMIN_H = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

BINANCE_BOTS = [
    'bot_1779131132692_3d47eb9b',   # Active futures
    'bot_1778971251604',             # Inactive
    'bot_1779029679564_b8070b61',    # Inactive
]

# 1. Login for later API calls
s = requests.post(BASE + '/api/user/login',
    json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'}, timeout=20)
token = s.json().get('session_token', '')
UID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'
USER_H = {'X-Session-Token': token, 'Content-Type': 'application/json'}
print(f"Login: {'OK' if token else 'FAIL'}")

# 2. Delete from all DB tables
conn = sqlite3.connect('C:/backend/zwesta_trading.db')
cur = conn.cursor()
now = datetime.now(timezone.utc).isoformat()

tables = [
    'bot_credentials',
    'bot_strategies',
    'bot_activation_pins',
    'bot_deletion_tokens',
    'bot_monitoring',
    'worker_bot_assignments',
    'worker_bot_queue',
    'binance_orders',
]

for bot_id in BINANCE_BOTS:
    for tbl in tables:
        try:
            cur.execute(f"DELETE FROM {tbl} WHERE bot_id=?", (bot_id,))
            if cur.rowcount:
                print(f"  deleted {cur.rowcount} from {tbl} for {bot_id}")
        except Exception as e:
            pass  # table may not have bot_id column

    # Soft-delete trades (keep history but mark cancelled)
    cur.execute("UPDATE trades SET status='cancelled' WHERE bot_id=? AND status IN ('open','pending')", (bot_id,))
    if cur.rowcount:
        print(f"  cancelled {cur.rowcount} open trades for {bot_id}")

    # Delete from user_bots last (FK parent)
    cur.execute("DELETE FROM user_bots WHERE bot_id=?", (bot_id,))
    print(f"  user_bots deleted: {cur.rowcount} for {bot_id}")

conn.commit()
conn.close()
print("\nDB cleanup done.")

# 3. Prune from in-memory active_bots
r = requests.post(f'{BASE}/api/bots/runtime/prune-ghosts', headers=USER_H, timeout=15)
print(f"prune-ghosts: {r.status_code} {r.text[:200]}")

# 4. Verify
time.sleep(2)
r = requests.get(f'{BASE}/api/bot/status', headers=USER_H, timeout=15)
bots = r.json() if isinstance(r.json(), list) else r.json().get('bots', [])
print(f"\nRemaining bots: {len(bots)}")
for b in bots:
    print(f"  {b.get('botId')}: {b.get('broker_type')} | {b.get('status')}")
