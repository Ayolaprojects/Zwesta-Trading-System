#!/usr/bin/env python3
"""Reset stale account-profit-staircase / equity-high-watermark state on bots.

Why this exists
---------------
The live risk engine arms an "account profit staircase" (a.k.a. surge guard) that
locks in a share of peak account equity. If a bot persisted a phantom peak equity
that is far above the real current balance, every new entry is blocked with:

    [RISK] Bot ... skipping ...: account profit staircase floor active:
    current equity $503.13 is below locked floor $22395.87 after peak $26266.92

The locked floor and watermark live in the per-bot ``runtime_state`` JSON in the
``user_bots`` table (fields ``accountProfitStaircase`` and
``accountEquityHighWatermark``). Clearing them lets the bot re-baseline at its
real current equity on the next trade cycle; the staircase then re-arms correctly
only after genuine new gains.

This script is read-only by default (dry run). Pass --apply to write changes.

Usage
-----
  python _reset_profit_staircase.py                 # dry run, show all affected bots
  python _reset_profit_staircase.py --apply         # apply to every affected bot
  python _reset_profit_staircase.py --bot bot_123   # limit to one bot (dry run)
  python _reset_profit_staircase.py --bot bot_123 --apply
  python _reset_profit_staircase.py --live-only      # only bots flagged is_live=1

It auto-detects PostgreSQL vs SQLite using the same runtime_infrastructure helper
the backend uses, so it targets whichever database the live backend is on.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

import runtime_infrastructure as ri

# Fields that hold the (potentially phantom) protective state we want to clear.
FIELDS_TO_CLEAR = (
    "accountProfitStaircase",
    "accountEquityHighWatermark",
    "drawdownPauseUntil",
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _connect() -> Tuple[Any, bool]:
    """Return (connection, is_postgres)."""
    if ri.using_postgres():
        database_url = ri.get_database_url()
        if not database_url:
            raise RuntimeError("PostgreSQL mode is enabled but DATABASE_URL is empty")
        try:
            import psycopg2
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("psycopg2 is required for PostgreSQL mode") from exc
        return psycopg2.connect(database_url), True

    conn = ri.build_sqlite_connection(ri.get_database_path())
    return conn, False


def _fetch_bots(conn: Any, is_postgres: bool, live_only: bool, bot_id: Optional[str]) -> List[Dict[str, Any]]:
    cursor = conn.cursor()
    where: List[str] = []
    params: List[Any] = []
    ph = "%s" if is_postgres else "?"
    if live_only:
        where.append("is_live = 1")
    if bot_id:
        where.append(f"bot_id = {ph}")
        params.append(bot_id)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    cursor.execute(
        f"SELECT bot_id, runtime_state, is_live, broker_account_id FROM user_bots{clause}",
        params,
    )
    rows = cursor.fetchall()
    cursor.close()

    bots: List[Dict[str, Any]] = []
    for row in rows:
        bots.append(
            {
                "bot_id": row[0],
                "runtime_state_raw": row[1],
                "is_live": row[2],
                "broker_account_id": row[3],
            }
        )
    return bots


def _describe_state(state: Dict[str, Any]) -> str:
    staircase = state.get("accountProfitStaircase")
    parts: List[str] = []
    if isinstance(staircase, dict):
        parts.append(
            "staircase[armed=%s breached=%s peak=%.2f floor=%.2f current=%.2f]"
            % (
                staircase.get("armed"),
                staircase.get("breached"),
                _safe_float(staircase.get("peakEquity")),
                _safe_float(staircase.get("lockedEquityFloor")),
                _safe_float(staircase.get("currentEquity")),
            )
        )
    if state.get("accountEquityHighWatermark") is not None:
        parts.append("equityHWM=%.2f" % _safe_float(state.get("accountEquityHighWatermark")))
    if state.get("drawdownPauseUntil"):
        parts.append("drawdownPauseUntil=%s" % state.get("drawdownPauseUntil"))
    return ", ".join(parts) if parts else "(no protective state)"


def _bot_needs_reset(state: Dict[str, Any]) -> bool:
    if not isinstance(state, dict):
        return False
    staircase = state.get("accountProfitStaircase")
    if isinstance(staircase, dict) and (
        staircase.get("armed") or staircase.get("breached") or _safe_float(staircase.get("peakEquity")) > 0
    ):
        return True
    if _safe_float(state.get("accountEquityHighWatermark")) > 0:
        return True
    if state.get("drawdownPauseUntil"):
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset stale profit-staircase / watermark state")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry run)")
    parser.add_argument("--bot", help="Limit to a single bot_id")
    parser.add_argument("--live-only", action="store_true", help="Only bots with is_live=1")
    args = parser.parse_args()

    summary = ri.get_runtime_infrastructure_summary()
    print("Database backend : %s" % summary.get("database_backend"))
    print("Postgres mode    : %s" % summary.get("postgres_mode"))
    print("Mode             : %s\n" % ("APPLY (writing changes)" if args.apply else "DRY RUN (no changes)"))

    conn, is_postgres = _connect()
    ph = "%s" if is_postgres else "?"
    try:
        bots = _fetch_bots(conn, is_postgres, args.live_only, args.bot)
    except Exception as exc:
        print("ERROR reading user_bots: %s" % exc)
        conn.close()
        return 2

    affected = 0
    updated = 0
    cursor = conn.cursor()
    for bot in bots:
        raw = bot["runtime_state_raw"]
        if not raw:
            continue
        try:
            state = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if not isinstance(state, dict):
            continue
        if not _bot_needs_reset(state):
            continue

        affected += 1
        print("Bot %s (live=%s, account=%s)" % (bot["bot_id"], bot["is_live"], bot["broker_account_id"]))
        print("  BEFORE: %s" % _describe_state(state))

        for field in FIELDS_TO_CLEAR:
            state.pop(field, None)
        # Leave accountProfitStaircaseEnabled as-is so the guard re-arms naturally
        # from the real current equity baseline on the next trade cycle.

        print("  AFTER : %s" % _describe_state(state))

        if args.apply:
            new_raw = json.dumps(state)
            cursor.execute(
                f"UPDATE user_bots SET runtime_state = {ph} WHERE bot_id = {ph}",
                (new_raw, bot["bot_id"]),
            )
            updated += 1
        print()

    if args.apply:
        conn.commit()
    cursor.close()
    conn.close()

    print("-" * 60)
    print("Bots scanned     : %d" % len(bots))
    print("Bots affected    : %d" % affected)
    if args.apply:
        print("Bots updated     : %d" % updated)
        print("\nDONE. Restart the backend so bots reload the cleaned runtime_state.")
    else:
        print("\nDry run only. Re-run with --apply to write these changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
