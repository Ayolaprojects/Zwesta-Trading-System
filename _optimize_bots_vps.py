"""
Bot Optimization Script — run this ON THE VPS (C:\backend folder).
Applies signal threshold and config fixes to both Binance and Exness bots.
"""
import sqlite3, json, shutil, os
from datetime import datetime

DB_PATH = r"C:\backend\zwesta_trading.db"

def main():
    # Backup first
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = DB_PATH.replace(".db", f"_BACKUP_{ts}.db")
    shutil.copy2(DB_PATH, backup)
    print(f"Backup created: {backup}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Check integrity
    cur.execute("PRAGMA integrity_check")
    ic = cur.fetchone()[0]
    if ic != "ok":
        print(f"WARNING: DB integrity check returned: {ic}")
        print("Attempting recovery via dump/reload...")
        conn.close()
        _recover_db(DB_PATH, backup)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

    optimizations = {
        # Binance futures bot — was signalThreshold=30 (too low), effectivePositionSizeMultiplier=0.45
        "bot_1779229018996": {
            "signalThreshold": 65,
            "managementProfile": "fast_growth",
            "maxOpenPositions": 1,
            "maxPositionsPerSymbol": 1,
            "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "effectivePositionSizeMultiplier": 1.0,
        },
        # Exness bot 1 — upgrade profile from beginner
        "bot_1779663832148": {
            "managementProfile": "fast_growth",
            "signalThreshold": 65,
        },
        # Exness bot 2 — raise threshold from 60
        "bot_1779676762137": {
            "signalThreshold": 65,
        },
        # Exness bot 3 — was losing, remove GBPUSDm (traded by other bot), add EURUSDm
        "bot_1779698254543": {
            "signalThreshold": 65,
            "symbols": ["US30m", "AMDm", "EURUSDm"],
        },
        # Exness bot 4 (duplicate of bot 3) — reassign to unique symbols
        "bot_1779698380843_043c7e5d": {
            "signalThreshold": 65,
            "symbols": ["USTECm", "EURUSDm", "USDJPYm"],
        },
    }

    for bot_id, updates in optimizations.items():
        cur.execute("SELECT runtime_state FROM user_bots WHERE bot_id = ?", (bot_id,))
        row = cur.fetchone()
        if not row:
            print(f"  SKIP (not found): {bot_id}")
            continue
        rs = json.loads(row["runtime_state"] or "{}")
        before = {k: rs.get(k) for k in updates}
        rs.update(updates)
        cur.execute("UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?",
                    (json.dumps(rs), bot_id))
        print(f"  UPDATED {bot_id}")
        for k, v in updates.items():
            print(f"    {k}: {before.get(k)} → {v}")
        print()

    conn.commit()
    conn.close()
    print("All changes committed. DB integrity:", _check_integrity(DB_PATH))


def _check_integrity(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    r = cur.fetchone()[0]
    conn.close()
    return r


def _recover_db(db_path, original_backup):
    """Recover a malformed SQLite database via dump/reload."""
    dump_path = db_path + ".dump.sql"
    recovered_path = db_path + ".recovered"

    src = sqlite3.connect(original_backup)
    with open(dump_path, "w", encoding="utf-8") as f:
        for line in src.iterdump():
            f.write(line + "\n")
    src.close()

    dst = sqlite3.connect(recovered_path)
    with open(dump_path, "r", encoding="utf-8") as f:
        dst.executescript(f.read())
    dst.close()
    os.replace(recovered_path, db_path)
    os.remove(dump_path)
    print("DB recovered from dump.")


if __name__ == "__main__":
    main()
