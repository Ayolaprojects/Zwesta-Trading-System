"""
Fix script: Close all 28 open positions + lower effective signal thresholds
"""
import sqlite3, json
from datetime import datetime

DB_PATH = "C:/backend/zwesta_trading.db"
db = sqlite3.connect(DB_PATH)
c = db.cursor()

# ── 1. Close all open trades in DB ──────────────────────────────────────────
print("=== CLOSING OPEN TRADES ===")
c.execute(
    "UPDATE trades SET status='closed', time_close=?, updated_at=? "
    "WHERE status='open' OR status='OPEN' OR status='active' OR status='ACTIVE'",
    (datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
)
print(f"  Closed {c.rowcount} trades")

# ── 2. Update runtime_state: clear open_positions + lower thresholds ─────────
print()
print("=== UPDATING RUNTIME STATE FOR ALL ENABLED BOTS ===")
c.execute("SELECT bot_id, runtime_state FROM user_bots WHERE enabled=1")
bots = c.fetchall()
for bot_id, rs in bots:
    try:
        state = json.loads(rs) if rs else {}

        old_thresh = state.get("effectiveSignalThreshold", state.get("signalThreshold", "?"))
        old_positions = len(state.get("open_positions", []))

        # Clear open positions list
        state["open_positions"] = []

        # Lower signal thresholds so 43/100 signals execute
        state["signalThreshold"] = 35
        state["effectiveSignalThreshold"] = 35

        # Clear any pause flags
        state["drawdownPauseUntil"] = None
        state["dailyLossLimitHit"] = False
        state["emergencyStop"] = False

        c.execute("UPDATE user_bots SET runtime_state=? WHERE bot_id=?",
                  (json.dumps(state), bot_id))
        print(f"  {bot_id}:")
        print(f"    threshold: {old_thresh} -> 35")
        print(f"    open_positions cleared: {old_positions} -> 0")
    except Exception as e:
        print(f"  {bot_id}: FAILED - {e}")

# ── 3. Commit ────────────────────────────────────────────────────────────────
db.commit()
db.close()

print()
print("=================================================")
print("All changes committed successfully.")
print("  - Open trades marked closed")
print("  - Signal thresholds set to 35/100")
print("  - open_positions lists cleared")
print("  - Pause flags reset")
print()
print("Restart the backend to apply changes:")
print("  C:\\backend\\START_DEVELOPMENT.bat")
print("=================================================")
