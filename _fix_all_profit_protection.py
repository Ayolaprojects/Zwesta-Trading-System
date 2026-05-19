"""
Permanent profitProtection fix:
  1. Stop all active bots via API
  2. Patch DB for all bots (Binance + Exness) with the $60+ performance settings
  3. Restart all bots

After this the bots run with the correct values in memory and write them back to DB
each cycle — making the fix SELF-SUSTAINING without any backend deployment.

Run from: c:\zwesta-trader\
"""
import sqlite3, json, requests, time

VPS     = 'http://148.113.5.39:9000'
DB      = r'C:\backend\zwesta_trading.db'
USER_ID = '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

# ── Auth ────────────────────────────────────────────────────────────────────
r = requests.post(f'{VPS}/api/user/login',
                  json={'email': 'zwexman@gmail.com', 'password': 'Zwesta1985'},
                  timeout=15)
TOKEN   = r.json()['session_token']
HEADERS = {'X-Session-Token': TOKEN}
print(f"Logged in. Token: {TOKEN[:16]}…\n")

# ── Target bots (all active: Binance + Exness) ───────────────────────────────
# These are the bots that appear in runtime_state with bad profitProtection values
ALL_BOTS = [
    'bot_1778970971191',             # Binance Spot demo
    'bot_1778971251604',             # Binance (2nd)
    'bot_1779029679564_b8070b61',    # Binance (3rd)
    'bot_1779029733318_cf548079',    # Binance (4th)
    'bot_1778970611374',             # Exness live
    'bot_1779011553325',             # Exness live (2nd)
]

# ── The $60+ profit-protection settings ─────────────────────────────────────
GOOD_PP = {
    'enabled': True,
    'activationPercent': 3.0,
    'activationMinProfit': 2.0,
    'portfolioActivationMinProfit': 3.0,
    'breakEvenBufferProfit': 10.0,      # was 0.5 — needs $10 profit before closing
    'breakEvenActivationShare': 0.30,   # was 0.5 — arms at 30% of peak
    'minLockedProfit': 5.0,             # was 0.0 — always keep $5 floor
    'retraceClosePercent': 10.0,        # was 22.0 — tighter trailing (keep 90%)
    'peakProfitHardLockShare': 0.90,    # was 0.95 — hard lock at 90% drop
    'closeLosingPositionsWithProfitablePeers': True,
    'loserRotationMinLoss': 0.0,
    'marginTakeProfitPercent': 30.0,
    'switchOnReversal': True,
    'adaptiveByVolatility': True,
    'breakEvenLockEnabled': True,
    'zeroLossLockEnabled': True,
    'minimumHoldMinutes': 1.0,
    'protectedSymbolCooldownMinutes': 5.0,
}


def stop_bot(bot_id):
    try:
        r = requests.post(f'{VPS}/api/bot/stop/{bot_id}', headers=HEADERS, timeout=15)
        if r.status_code == 200:
            print(f"  ✓ Stopped {bot_id}")
            return True
        else:
            print(f"  ✗ Stop failed {bot_id}: {r.status_code} {r.text[:80]}")
            return False
    except Exception as e:
        print(f"  ✗ Stop error {bot_id}: {e}")
        return False


def start_bot(bot_id):
    try:
        r = requests.post(f'{VPS}/api/bot/start', headers=HEADERS,
                          json={'botId': bot_id, 'user_id': USER_ID}, timeout=20)
        if r.status_code == 200:
            print(f"  ✓ Started {bot_id}")
            return True
        else:
            print(f"  ✗ Start failed {bot_id}: {r.status_code} {r.text[:120]}")
            return False
    except Exception as e:
        print(f"  ✗ Start error {bot_id}: {e}")
        return False


def patch_db(bot_ids):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    patched = []
    for bot_id in bot_ids:
        try:
            row = conn.execute(
                "SELECT rowid, runtime_state FROM user_bots WHERE bot_id=?", (bot_id,)
            ).fetchone()
            if not row:
                print(f"  [DB] {bot_id}: NOT FOUND")
                continue
            rs_raw = row['runtime_state']
            if not rs_raw:
                print(f"  [DB] {bot_id}: no runtime_state, skipping")
                continue
            rs = json.loads(rs_raw)
            old = rs.get('profitProtection', {}).get('breakEvenBufferProfit', '?')
            rs['profitProtection'] = GOOD_PP
            conn.execute("UPDATE user_bots SET runtime_state=? WHERE rowid=?",
                         (json.dumps(rs), row['rowid']))
            conn.commit()
            patched.append(bot_id)
            print(f"  [DB] {bot_id}: breakEvenBufferProfit {old} → 10.0  ✓")
        except Exception as e:
            print(f"  [DB] {bot_id}: ERROR — {e}")
    conn.close()
    return patched


# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 — Stop all bots")
print("=" * 60)
stopped = []
for bot_id in ALL_BOTS:
    if stop_bot(bot_id):
        stopped.append(bot_id)

print(f"\nWaiting 8 s for bots to fully stop…")
time.sleep(8)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 — Patch DB (bots are stopped, no overwrites)")
print("=" * 60)
patched = patch_db(ALL_BOTS)

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 — Restart all bots")
print("=" * 60)
restarted = []
for bot_id in ALL_BOTS:
    if start_bot(bot_id):
        restarted.append(bot_id)
    time.sleep(1)  # small gap between starts

# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Stopped:   {len(stopped)}/{len(ALL_BOTS)}")
print(f"Patched:   {len(patched)}/{len(ALL_BOTS)}")
print(f"Restarted: {len(restarted)}/{len(ALL_BOTS)}")

if len(restarted) == len(ALL_BOTS):
    print("\n✓ ALL BOTS now running with the $60+ profitProtection settings.")
    print("  The fix is self-sustaining — bots write these values back to DB each cycle.")
    print("  Even after a VPS restart, the bots will reload the correct values from DB.")
else:
    missing = [b for b in ALL_BOTS if b not in restarted]
    print(f"\n⚠ Some bots did not restart: {missing}")
    print("  Re-run this script or start them manually via the app.")

print("\nKey values active:")
print(f"  breakEvenBufferProfit  = 10.0  (was 0.5)")
print(f"  retraceClosePercent    = 10.0  (was 22.0)")
print(f"  minLockedProfit        = 5.0   (was 0.0)")
print(f"  breakEvenActivationShare = 0.30 (was 0.5)")
