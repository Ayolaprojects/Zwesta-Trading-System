import sqlite3, json, requests
from datetime import datetime, timezone

BOT_ID = 'bot_1779131132692_3d47eb9b'
BASE = 'http://148.113.5.39:9000'
KEY = 'zwesta_live_api_key_2026_secure'

# New symbols: all viable for 10.87 USDT notional on futures
# SOL (OK), XRP (OK), ADA (OK), BNB (OK) - all pass min lot checks
NEW_SYMBOLS = 'SOLUSDT,XRPUSDT,ADAUSDT,BNBUSDT'

conn = sqlite3.connect('C:/backend/zwesta_trading.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
now = datetime.now(timezone.utc).isoformat()

# Update symbols in user_bots
cur.execute("UPDATE user_bots SET symbols=?, updated_at=? WHERE bot_id=?", (NEW_SYMBOLS, now, BOT_ID))
print(f"symbols updated: {cur.rowcount} row(s)")

# Patch runtime_state: fix maxDailyLoss back to 80, update symbols list
cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id=?", (BOT_ID,))
row = cur.fetchone()
if row and row['runtime_state']:
    rs = json.loads(row['runtime_state'])
    rs['maxDailyLoss'] = 80.0
    rs['symbols'] = NEW_SYMBOLS.split(',')
    cur.execute("UPDATE user_bots SET runtime_state=? WHERE bot_id=?", (json.dumps(rs), BOT_ID))
    print("runtime_state: maxDailyLoss=80, symbols updated")

conn.commit()
conn.close()
print("DB committed.")

# Patch via admin API (updates in-memory active_bots too)
headers = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}
r = requests.post(f'{BASE}/api/admin/fix-bot-link', headers=headers, json={
    'bot_id': BOT_ID,
    'runtime_state': {
        'maxDailyLoss': 80.0,
        'symbols': NEW_SYMBOLS.split(','),
    }
})
print(f"fix-bot-link: {r.status_code} {r.text[:200]}")


