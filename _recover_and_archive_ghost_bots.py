import json
import os
import shutil
import sqlite3
from datetime import datetime

SRC = r"C:\backend\zwesta_trading.db"
TS = datetime.now().strftime("%Y%m%d_%H%M%S")
RECOVERED = rf"C:\backend\zwesta_trading.ghost_pruned_{TS}.db"
BACKUP = rf"C:\backend\zwesta_trading.pre_ghost_prune_{TS}.db"


def recover_db(src: str, dst: str) -> None:
    if os.path.exists(dst):
        os.remove(dst)

    src_conn = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    src_conn.row_factory = sqlite3.Row
    try:
        src_conn.execute("PRAGMA writable_schema = ON")
    except Exception:
        pass
    try:
        src_conn.execute("PRAGMA cell_size_check = OFF")
    except Exception:
        pass

    dst_conn = sqlite3.connect(dst)
    dst_conn.execute("PRAGMA journal_mode = WAL")
    dst_conn.execute("PRAGMA synchronous = NORMAL")
    dst_conn.execute("PRAGMA foreign_keys = OFF")

    try:
        schema_objects = src_conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
            "ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 WHEN 'trigger' THEN 2 WHEN 'view' THEN 3 ELSE 4 END"
        ).fetchall()

        created_tables = []
        deferred = []
        for typ, name, tbl_name, sql in schema_objects:
            if typ != "table":
                deferred.append((typ, name, tbl_name, sql))
                continue
            try:
                dst_conn.execute(sql)
                created_tables.append(name)
            except Exception as exc:
                print(f"[SKIP TABLE CREATE] {name}: {exc}")

        for name in created_tables:
            try:
                cols = src_conn.execute(f'PRAGMA table_info("{name}")').fetchall()
            except Exception as exc:
                print(f"[SKIP TABLE INFO] {name}: {exc}")
                continue

            if not cols:
                continue

            placeholders = ",".join(["?"] * len(cols))
            insert_sql = f'INSERT OR IGNORE INTO "{name}" VALUES ({placeholders})'

            try:
                rows = src_conn.execute(f'SELECT * FROM "{name}"').fetchall()
                dst_conn.executemany(insert_sql, rows)
                dst_conn.commit()
                print(f"[COPY] {name}: {len(rows)} rows")
            except Exception as bulk_exc:
                dst_conn.rollback()
                ok = 0
                err = 0
                try:
                    rowids = [row[0] for row in src_conn.execute(f'SELECT rowid FROM "{name}"').fetchall()]
                    for rowid in rowids:
                        try:
                            row = src_conn.execute(f'SELECT * FROM "{name}" WHERE rowid = ?', (rowid,)).fetchone()
                            if row is not None:
                                dst_conn.execute(insert_sql, row)
                                ok += 1
                        except Exception:
                            err += 1
                    dst_conn.commit()
                    print(f"[RECOVER] {name}: ok={ok} err={err} bulk_err={bulk_exc}")
                except Exception as row_exc:
                    print(f"[FAIL] {name}: bulk_err={bulk_exc} row_err={row_exc}")

        for typ, name, tbl_name, sql in deferred:
            try:
                dst_conn.execute(sql)
            except Exception as exc:
                print(f"[SKIP {typ.upper()}] {name}: {exc}")

        dst_conn.commit()
        integrity = dst_conn.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"[RECOVERED INTEGRITY] {integrity}")
    finally:
        src_conn.close()
        dst_conn.close()


def _load_runtime_state(raw: str) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def archive_strict_ghosts(db_path: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    archived = []
    try:
        cursor = conn.cursor()
        bot_rows = cursor.execute(
            "SELECT bot_id, user_id, name, status, enabled, runtime_state, created_at FROM user_bots WHERE status = 'active'"
        ).fetchall()

        for row in bot_rows:
            bot_id = row["bot_id"]
            runtime_state = _load_runtime_state(row["runtime_state"])
            open_positions = runtime_state.get("open_positions") if isinstance(runtime_state.get("open_positions"), dict) else {}
            open_trades = 0
            total_trades = 0
            try:
                open_trades = cursor.execute(
                    "SELECT COUNT(*) FROM trades WHERE bot_id = ? AND LOWER(COALESCE(status, '')) = 'open'",
                    (bot_id,),
                ).fetchone()[0] or 0
            except Exception:
                open_trades = 0
            try:
                total_trades = cursor.execute(
                    "SELECT COUNT(*) FROM trades WHERE bot_id = ?",
                    (bot_id,),
                ).fetchone()[0] or 0
            except Exception:
                total_trades = 0

            is_enabled = bool(row["enabled"])
            has_runtime_open = bool(open_positions)
            if is_enabled or has_runtime_open or open_trades or total_trades:
                continue

            cleaned_state = dict(runtime_state)
            cleaned_state["open_positions"] = {}
            cleaned_state["tradeHistory"] = []
            cleaned_state["profitHistory"] = []
            cleaned_state["dailyProfits"] = {}
            cleaned_state["lastNoTradeReason"] = "archived_strict_ghost_cleanup"

            cursor.execute(
                "UPDATE user_bots SET status = ?, runtime_state = ?, updated_at = ? WHERE bot_id = ?",
                (
                    "archived",
                    json.dumps(cleaned_state, separators=(",", ":")),
                    datetime.now().isoformat(),
                    bot_id,
                ),
            )
            archived.append(
                {
                    "bot_id": bot_id,
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "created_at": row["created_at"],
                }
            )

        conn.commit()
        print(f"[ARCHIVED STRICT GHOSTS] {len(archived)}")
        for item in archived[:25]:
            print(f"  - {item['bot_id']} | user={item['user_id']} | name={item['name']} | created={item['created_at']}")

        integrity = cursor.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"[CLEANED INTEGRITY] {integrity}")
        return archived
    finally:
        conn.close()


def replace_live_db(recovered: str, src: str, backup: str) -> None:
    shutil.copy2(src, backup)
    replacement = src + ".replacement"
    if os.path.exists(replacement):
        os.remove(replacement)
    shutil.copy2(recovered, replacement)
    try:
        os.replace(replacement, src)
    except PermissionError as exc:
        print(f"[LIVE REPLACE BLOCKED] {exc}")
        print(f"[LIVE REPLACE BLOCKED] The recovered DB is ready at: {recovered}")
        print(f"[LIVE REPLACE BLOCKED] Backup copy of the current live DB is at: {backup}")
        return

    for suffix in ("-wal", "-shm"):
        sidecar = src + suffix
        if os.path.exists(sidecar):
            try:
                os.remove(sidecar)
            except Exception as exc:
                print(f"[WARN] Could not remove sidecar {sidecar}: {exc}")

    conn = sqlite3.connect(src)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"[LIVE INTEGRITY AFTER REPLACE] {result}")
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"[SOURCE] {SRC}")
    print(f"[RECOVERED TARGET] {RECOVERED}")
    print(f"[BACKUP TARGET] {BACKUP}")

    recover_db(SRC, RECOVERED)
    archived = archive_strict_ghosts(RECOVERED)
    replace_live_db(RECOVERED, SRC, BACKUP)

    print(f"[DONE] archived={len(archived)} recovered={RECOVERED} backup={BACKUP}")
