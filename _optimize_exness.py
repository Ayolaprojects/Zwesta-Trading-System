"""Exness/MT5 optimizer: tighten over-trading.

Sets all MT5/Exness bots for the active user to a more selective signal
threshold (default 65, manual mode) and configures a 60-minute post-close
cooldown so the bot does NOT immediately re-open a position after the user
manually closes it in MT5 (or after a TP/SL hit).

The post-close cooldown gate is implemented in
multi_broker_backend_updated.py (per-symbol cooldown stored in
bot_config['symbol_cooldown_until']). This script just toggles the
configurable knob `postCloseCooldownMinutes`.

Usage:
    # Local
    python _optimize_exness.py
    # VPS (after RDP)
    cd C:\\backend && python _optimize_exness.py
"""
import json
import sqlite3
import sys
from datetime import datetime

DB = r'C:\backend\zwesta_trading.db'
NOW = datetime.now().isoformat()

# Same user as the other optimize scripts. Override via CLI arg if needed.
USER = sys.argv[1] if len(sys.argv) > 1 else '8e74db37-fd1e-4c57-87c4-ad3b64012ecf'

PATCH = {
    # Be selective: was effectively floor=1 (every signal >= 1 passed), now require 65/100.
    'signalThreshold': 65,
    'effectiveSignalThreshold': 65,
    'signalThresholdMode': 'manual',
    'autoSwitch': False,
    'autoAdaptationEnabled': False,
    'allowAdaptiveRawFallback': False,
    'intelligentScanner': False,
    'adaptiveSignalThresholdOffset': 0,
    'adaptiveSignalMissCount': 0,
    'adaptiveSignalThresholdReason': None,

    # 60-minute post-close cooldown: stops the bot from re-opening on the
    # same symbol immediately after a manual close in MT5 or a TP/SL hit.
    'postCloseCooldownMinutes': 60,

    # Clear any stale cooldown markers so the new setting starts clean.
    'symbol_cooldown_until': {},

    # Reset transient pause/loss-streak state so we start clean.
    'managementState': 'normal',
    'consecutiveLosses': 0,
    'lossStreakPauseUntil': None,
    'pauseReason': None,
    'drawdownPauseUntil': None,
    'drawdownPauseSetAt': None,
}


def _is_exness_or_mt5(broker_account_id: str) -> bool:
    if not broker_account_id:
        return False
    bid = broker_account_id.lower()
    return bid.startswith('mt5_') or bid.startswith('exness_') or 'exness' in bid or 'mt5' in bid


def main() -> int:
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    cur = c.cursor()

    rows = cur.execute(
        "SELECT bot_id, broker_account_id, runtime_state FROM user_bots WHERE user_id = ?",
        (USER,),
    ).fetchall()

    patched = 0
    skipped = 0
    for r in rows:
        bid = r['bot_id']
        broker_acc = r['broker_account_id'] or ''
        if not _is_exness_or_mt5(broker_acc):
            skipped += 1
            continue
        s = json.loads(r['runtime_state'] or '{}')
        s.update(PATCH)
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
            (json.dumps(s), NOW, bid),
        )
        patched += 1
        print(f"[EXNESS-OPT] {bid} ({broker_acc}): threshold=65 manual + 60m post-close cooldown")

    c.commit()
    c.close()
    print(f"\nDone. Patched {patched} Exness/MT5 bot(s); skipped {skipped} non-MT5 bot(s).")
    print("Restart backend for changes to take effect.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
