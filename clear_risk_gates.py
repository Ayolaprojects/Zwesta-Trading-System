"""
Zwesta Trader — Risk Gate Cleanup & SOLUSDT Threshold Tuning
============================================================
Run this ON THE VPS (or wherever zwesta_trading.db lives) to:
  1. Clear stale risk gates that are silently blocking trades:
       - lossStreakPauseUntil
       - drawdownPauseUntil
       - symbolReentryCooldowns (all symbols)
       - pauseReason / status=PAUSED
  2. Lower the per-bot signal threshold for SOLUSDT (and base
     'signalThreshold') so that qualifying setups actually pass
     the entry filter.

Safe to run multiple times. Backs up runtime_state to JSON before changes.

Usage:
    python clear_risk_gates.py                    # dry-run (default), prints actions only
    python clear_risk_gates.py --apply            # actually write changes
    python clear_risk_gates.py --apply --threshold 50
                                                  # also force SOLUSDT signal threshold to 50
    python clear_risk_gates.py --apply --db /path/to/zwesta_trading.db

After running with --apply, RESTART THE WORKER PROCESS so it
reloads the runtime_state from the DB.
"""
import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime

DEFAULT_DB = r'C:\backend\zwesta_trading.db'
SOL_TARGETS = ("SOLUSDT", "SOLBNB", "SOL")

GATE_KEYS_NULLABLE = ("lossStreakPauseUntil", "drawdownPauseUntil")


def backup_state(rows, db_path):
    backup_path = f"{db_path}.runtime_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = [{"bot_id": r[0], "runtime_state": r[1]} for r in rows]
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[backup] wrote {backup_path}")


def affects_sol(symbols_csv: str) -> bool:
    if not symbols_csv:
        return False
    syms = {s.strip().upper() for s in symbols_csv.split(",") if s.strip()}
    return any(t in syms for t in SOL_TARGETS)


def clean_runtime(d: dict, sol_threshold: int | None) -> list[str]:
    """Mutate d in place. Return list of actions taken."""
    actions = []

    for k in GATE_KEYS_NULLABLE:
        if d.get(k):
            actions.append(f"cleared {k}={d[k]}")
            d[k] = None

    cooldowns = d.get("symbolReentryCooldowns")
    if isinstance(cooldowns, dict) and cooldowns:
        actions.append(f"cleared symbolReentryCooldowns ({len(cooldowns)} entries: {list(cooldowns)[:5]})")
        d["symbolReentryCooldowns"] = {}

    legacy_cd = d.get("symbol_cooldowns")
    if isinstance(legacy_cd, dict) and legacy_cd:
        actions.append(f"cleared symbol_cooldowns ({len(legacy_cd)} entries)")
        d["symbol_cooldowns"] = {}

    if d.get("pauseReason"):
        actions.append(f"cleared pauseReason='{d['pauseReason']}'")
        d["pauseReason"] = None

    if d.get("status") == "PAUSED":
        actions.append("status PAUSED -> active")
        d["status"] = "active"

    if d.get("adaptiveSignalThresholdOffset"):
        actions.append(f"reset adaptiveSignalThresholdOffset={d['adaptiveSignalThresholdOffset']}")
        d["adaptiveSignalThresholdOffset"] = 0

    if sol_threshold is not None:
        cur_thresh = d.get("signalThreshold")
        if cur_thresh is None or cur_thresh > sol_threshold:
            actions.append(f"signalThreshold {cur_thresh} -> {sol_threshold}")
            d["signalThreshold"] = sol_threshold

        per_sym = d.get("perSymbolSignalThreshold")
        if not isinstance(per_sym, dict):
            per_sym = {}
        for sym in ("SOLUSDT", "SOLBNB"):
            if per_sym.get(sym) != sol_threshold:
                actions.append(f"perSymbolSignalThreshold[{sym}] {per_sym.get(sym)} -> {sol_threshold}")
                per_sym[sym] = sol_threshold
        d["perSymbolSignalThreshold"] = per_sym

    return actions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB, help="Path to zwesta_trading.db")
    ap.add_argument("--apply", action="store_true", help="Actually write changes (otherwise dry-run)")
    ap.add_argument("--threshold", type=int, default=55,
                    help="Lower SOLUSDT signal threshold to this value (default 55). "
                         "Use 0 to skip threshold changes.")
    ap.add_argument("--only-sol", action="store_true",
                    help="Only touch bots whose symbols include SOLUSDT/SOLBNB")
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f"[error] DB not found: {args.db}", file=sys.stderr)
        sys.exit(2)

    sol_threshold = None if args.threshold <= 0 else args.threshold

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute("SELECT bot_id, runtime_state, symbols, status FROM user_bots")
    rows = cur.fetchall()
    print(f"[scan] {len(rows)} bot(s) found in {args.db}")

    backup_state([(b, rs) for b, rs, _, _ in rows], args.db)

    total_changes = 0
    updates = []
    for bot_id, rs, symbols_csv, db_status in rows:
        if args.only_sol and not affects_sol(symbols_csv or ""):
            continue
        if not rs:
            d = {}
        else:
            try:
                d = json.loads(rs)
            except json.JSONDecodeError as e:
                print(f"[skip] {bot_id}: runtime_state parse error: {e}")
                continue

        actions = clean_runtime(d, sol_threshold)
        if not actions and db_status != "PAUSED":
            continue

        total_changes += len(actions)
        print(f"\n--- {bot_id} (symbols={symbols_csv}) ---")
        for a in actions:
            print(f"  - {a}")
        if db_status == "PAUSED":
            print(f"  - user_bots.status PAUSED -> active")
        updates.append((bot_id, json.dumps(d)))

    if not args.apply:
        print(f"\n[dry-run] would change {total_changes} field(s) across {len(updates)} bot(s).")
        print("[dry-run] Re-run with --apply to commit.")
        conn.close()
        return

    for bot_id, new_rs in updates:
        cur.execute(
            "UPDATE user_bots SET runtime_state=?, status='active', updated_at=? WHERE bot_id=?",
            (new_rs, datetime.now().isoformat(), bot_id),
        )
    conn.commit()
    conn.close()
    print(f"\n[applied] updated {len(updates)} bot(s). RESTART THE WORKER NOW so it reloads runtime_state.")


if __name__ == "__main__":
    main()
