"""
Direct DB fix — run this ON THE VPS (e.g. via RDP) to fix all issues
without needing the API:

  1. Fix bot_1779100405400 is_live=0 (it uses a DEMO credential)
  2. Fix bot_1779057251465 tradeAmount=500 (R500 per trade, was R8)
  3. Fix broker_credentials account_currency='ZAR' for Exness live credential
  4. Fix broker_credentials account_currency='ZAR' for Exness demo credential
  5. Sync runtime_state JSON for tradeAmount change

Run:  python C:\\backend\\fix_db_direct.py
"""
import sqlite3, json
from datetime import datetime

DB_PATH = r'C:\backend\zwesta_trading.db'
LIVE_BOT    = 'bot_1779057251465'   # R1350 live  — must link to LIVE cred, tradeAmount=500
DEMO_BOT    = 'bot_1779100405400'   # R24k demo   — must link to DEMO cred, is_live=0
EXNESS_LIVE_CRED = '9f14c8b4-0071-4222-81a2-5c99e841b9e0'  # 295677214 REAL account
EXNESS_DEMO_CRED = '66838627-f045-489d-85d6-a81e829d4228'  # 435760376 TRIAL account

db = sqlite3.connect(DB_PATH, timeout=30)
db.row_factory = sqlite3.Row
db.execute('PRAGMA journal_mode=WAL')
db.execute('PRAGMA busy_timeout=15000')
cur = db.cursor()

now = datetime.now().isoformat()
changes = []

# ── 0. FIX CREDENTIAL SWAP — bot_credentials table ───────────────────────────
# bot_1779057251465 got swapped to demo cred; must point to live cred
# bot_1779100405400 must point to demo cred
for bot_id, expected_cred, label in [
    (LIVE_BOT, EXNESS_LIVE_CRED, 'LIVE cred (295677214)'),
    (DEMO_BOT, EXNESS_DEMO_CRED, 'DEMO cred (435760376)'),
]:
    cur.execute('SELECT credential_id FROM bot_credentials WHERE bot_id=?', (bot_id,))
    crow = cur.fetchone()
    if crow:
        old_cred = crow['credential_id']
        if old_cred != expected_cred:
            cur.execute('UPDATE bot_credentials SET credential_id=? WHERE bot_id=?',
                (expected_cred, bot_id))
            changes.append(f'  bot_credentials {bot_id[:28]}: cred → {label}')
        else:
            changes.append(f'  bot_credentials {bot_id[:28]}: already correct ✅')
    else:
        # Insert missing link
        cur.execute('INSERT INTO bot_credentials (bot_id, credential_id, user_id, created_at) VALUES (?,?,?,?)',
            (bot_id, expected_cred, '8e74db37-fd1e-4c57-87c4-ad3b64012ecf', now))
        changes.append(f'  bot_credentials {bot_id[:28]}: INSERTED → {label}')

# ── 1. Fix is_live for demo bot ───────────────────────────────────────────────
cur.execute('SELECT is_live FROM user_bots WHERE bot_id = ?', (DEMO_BOT,))
row = cur.fetchone()
if row:
    old = row['is_live']
    cur.execute('UPDATE user_bots SET is_live=0, updated_at=? WHERE bot_id=?', (now, DEMO_BOT))
    changes.append(f'  {DEMO_BOT}: is_live {old} → 0')
else:
    changes.append(f'  {DEMO_BOT}: NOT FOUND IN DB')

# ── 2. Fix tradeAmount for live bot ──────────────────────────────────────────
cur.execute('SELECT runtime_state, broker_account_id FROM user_bots WHERE bot_id = ?', (LIVE_BOT,))
row = cur.fetchone()
if row:
    try:
        rs = json.loads(row['runtime_state'] or '{}')
    except Exception:
        rs = {}
    old_ta = rs.get('tradeAmount', 'not in runtime_state')
    rs['tradeAmount'] = 500.0
    rs['displayCurrency'] = 'ZAR'
    rs['accountCurrency'] = 'ZAR'
    rs['credentialId'] = EXNESS_LIVE_CRED
    # Also fix broker_account_id in user_bots to match live account
    cur.execute('''UPDATE user_bots SET runtime_state=?, broker_account_id=?, updated_at=?
                   WHERE bot_id=?''',
        (json.dumps(rs), 'Exness_295677214', now, LIVE_BOT))
    changes.append(f'  {LIVE_BOT}: tradeAmount {old_ta} → 500.0 ZAR, broker_account_id → Exness_295677214')
else:
    changes.append(f'  {LIVE_BOT}: NOT FOUND IN DB')

# ── 3. Fix account_currency for Exness credentials ───────────────────────────
for cred_id, acct, curr in [
    (EXNESS_LIVE_CRED, '295677214', 'ZAR'),
    (EXNESS_DEMO_CRED, '435760376', 'ZAR'),
]:
    cur.execute('SELECT account_currency FROM broker_credentials WHERE credential_id=?', (cred_id,))
    crow = cur.fetchone()
    if crow:
        old_curr = crow['account_currency']
        cur.execute('UPDATE broker_credentials SET account_currency=?, updated_at=? WHERE credential_id=?',
            (curr, now, cred_id))
        changes.append(f'  credential {acct}: account_currency "{old_curr}" → "{curr}"')
    else:
        changes.append(f'  credential {acct}: NOT FOUND')

db.commit()
db.close()

print('✅ DB fixes applied:')
for c in changes:
    print(c)
print()
print('NOTE: Restart the backend process for runtime_state changes to take effect.')
print('      (tradeAmount in runtime_state is loaded on bot start)')
