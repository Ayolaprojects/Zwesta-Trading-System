"""
Symbol Expansion Script — run ON THE VPS (C:\backend).

Enables full-universe scanning on all active bots (Exness & Binance) so the
engine probes symbols beyond the initial list when signal quality degrades.

Changes applied per bot
─────────────────────────
  intelligentScanner         → True   (scan full broker universe every cycle)
  allowCrossMarketReallocation → True  (allow non-configured symbols to be traded)
  adaptiveSignalMissCount    → reset to 0  (fresh start on idle counter)
  adaptiveSignalThresholdOffset → 0
  symbolPerformance          → cleared  (forget stale per-symbol verdicts)

Binance bots additionally get the expanded symbol list:
  symbols → BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, ADAUSDT, DOGEUSDT
            (curated list — scanner will also probe the full ~60-symbol universe)
"""
import sqlite3
import json
import shutil
import os
from datetime import datetime

DB_PATH = r"C:\backend\zwesta_trading.db"

BINANCE_EXPANDED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
]

EXNESS_EXPANDED_SYMBOLS = [
    "EURUSDm", "GBPUSDm", "USDJPYm", "AUDUSDm",
    "XAUUSDm", "BTCUSDm", "ETHUSDm", "SOLUSDm",
    "US30m", "USTECm", "TSMm",
]


def _is_binance_bot(rs: dict, symbols: list) -> bool:
    broker = str(rs.get("brokerName") or rs.get("broker_type") or "").lower()
    if "binance" in broker:
        return True
    # Infer from symbols
    return any(str(s).upper().endswith("USDT") for s in symbols)


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.replace(".db", f"_BACKUP_expand_{ts}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup created: {backup}\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE enabled = 1 OR enabled = '1' OR enabled IS NULL")
    rows = cur.fetchall()

    updated = 0
    skipped = 0

    for row in rows:
        bot_id = row["bot_id"]
        rs = json.loads(row["runtime_state"] or "{}")

        symbols = rs.get("symbols") or []
        is_binance = _is_binance_bot(rs, symbols)

        changes = {}

        # 1. Enable intelligent scanner (full-universe probe every cycle)
        if not rs.get("intelligentScanner"):
            changes["intelligentScanner"] = True

        # 2. Allow cross-market reallocation (trade symbols outside initial list)
        if not rs.get("allowCrossMarketReallocation"):
            changes["allowCrossMarketReallocation"] = True

        # 3. Reset idle counters so expansion triggers immediately
        if rs.get("adaptiveSignalMissCount", 0) != 0:
            changes["adaptiveSignalMissCount"] = 0
        if rs.get("adaptiveSignalThresholdOffset", 0) != 0:
            changes["adaptiveSignalThresholdOffset"] = 0

        # 4. Clear stale per-symbol performance verdicts so new symbols get a fair chance
        if rs.get("symbolPerformance"):
            changes["symbolPerformance"] = {}

        # 5. Widen configured symbol list if currently too narrow
        if is_binance and len(symbols) < 5:
            current_bases = {s.upper().replace("USDT", "") for s in symbols}
            extra = [
                s for s in BINANCE_EXPANDED_SYMBOLS
                if s.replace("USDT", "") not in current_bases
            ]
            if extra:
                changes["symbols"] = symbols + extra[:max(0, 8 - len(symbols))]

        if not changes:
            skipped += 1
            continue

        rs.update(changes)
        cur.execute(
            "UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?",
            (json.dumps(rs), bot_id),
        )
        updated += 1
        broker_tag = "Binance" if is_binance else "Exness/MT5"
        print(f"  UPDATED [{broker_tag}] {bot_id}")
        for k, v in changes.items():
            if k == "symbols":
                print(f"    symbols: {symbols} → {v}")
            elif k == "symbolPerformance":
                print(f"    symbolPerformance: cleared")
            else:
                print(f"    {k}: {rs.get(k)} → {v}")
        print()

    conn.commit()
    conn.close()

    print(f"Done — {updated} bots updated, {skipped} already optimal / not changed.")
    print()
    print("What happens next:")
    print("  • Each bot will now scan the FULL broker symbol universe each cycle")
    print("  • Unexplored symbols (never tried) are injected AHEAD of familiar ones")
    print("  • Blacklisted symbols are skipped but retried every 4 h automatically")
    print("  • Restart the backend (or bots) for changes to take effect immediately")


if __name__ == "__main__":
    main()
