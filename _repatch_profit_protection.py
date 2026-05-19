"""
Re-patch profitProtection for ALL active Binance bots.
Also checks current state before and after.
Run this any time after a bot restart wipes the patch.
"""
import sqlite3, json

db = r'C:\backend\zwesta_trading.db'
BINANCE_BOTS = ['bot_1778970971191', 'bot_1778971251604',
                'bot_1779029679564_b8070b61', 'bot_1779029733318_cf548079']

PROFIT_PROTECTION_FIX = {
    'enabled': True,
    'activationPercent': 3.0,
    'activationMinProfit': 2.0,
    'portfolioActivationMinProfit': 3.0,
    'breakEvenBufferProfit': 10.0,      # KEY FIX: was 0.5
    'breakEvenActivationShare': 0.30,   # KEY FIX: was 0.5
    'minLockedProfit': 5.0,             # KEY FIX: was 0.0
    'retraceClosePercent': 10.0,        # KEY FIX: was 22.0
    'peakProfitHardLockShare': 0.90,    # KEY FIX: was 0.95
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

conn = sqlite3.connect(db)
conn.row_factory = sqlite3.Row

print("Patching profitProtection for Binance bots...\n")

for bot_id in BINANCE_BOTS:
    try:
        row = conn.execute(
            "SELECT rowid, runtime_state FROM user_bots WHERE bot_id=?", (bot_id,)
        ).fetchone()
        if not row:
            print(f"  {bot_id}: NOT FOUND in DB")
            continue

        rowid = row['rowid']
        rs_raw = row['runtime_state']
        if not rs_raw:
            print(f"  {bot_id}: no runtime_state yet")
            continue

        rs = json.loads(rs_raw)
        old_pp = rs.get('profitProtection', {})
        old_beb = old_pp.get('breakEvenBufferProfit', '?')
        old_rc = old_pp.get('retraceClosePercent', '?')
        old_mlp = old_pp.get('minLockedProfit', '?')

        # Apply fix
        rs['profitProtection'] = PROFIT_PROTECTION_FIX

        new_rs = json.dumps(rs)
        conn.execute(
            "UPDATE user_bots SET runtime_state=? WHERE rowid=?",
            (new_rs, rowid)
        )
        conn.commit()

        print(f"  {bot_id}: PATCHED")
        print(f"    breakEvenBufferProfit: {old_beb} → 10.0")
        print(f"    retraceClosePercent:   {old_rc} → 10.0")
        print(f"    minLockedProfit:       {old_mlp} → 5.0")

        # Verify
        check = json.loads(
            conn.execute("SELECT runtime_state FROM user_bots WHERE rowid=?", (rowid,)).fetchone()[0]
        )
        pp = check.get('profitProtection', {})
        ok = pp.get('breakEvenBufferProfit') == 10.0 and pp.get('retraceClosePercent') == 10.0
        print(f"    Verified: {'✓ OK' if ok else '✗ FAILED'}")

    except Exception as e:
        print(f"  {bot_id}: ERROR — {e}")

conn.close()
print("\nDone. Re-run this after any bot restart.")
