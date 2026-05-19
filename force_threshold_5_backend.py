"""
Force all bots in C:\\backend\\zwesta_trading.db to use signal threshold 5
by switching them to manual mode (bypasses adaptive/recovery overrides).
"""
import sqlite3
import json

DB_PATH = r'C:\backend\zwesta_trading.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT bot_id, name, runtime_state FROM user_bots')
rows = cursor.fetchall()

updated = 0
for bot_id, name, rs in rows:
    state = json.loads(rs) if rs else {}

    # Force manual mode so user-set threshold isn't overridden
    state['managementMode'] = 'manual'
    state['signalThresholdMode'] = 'manual'

    # Set thresholds to 5
    state['signalThreshold'] = 5
    state['effectiveSignalThreshold'] = 5

    # Clear adaptive overrides
    state['adaptiveSignalThresholdOffset'] = 0
    state['adaptiveSignalMissCount'] = 0
    state['adaptiveSignalThresholdReason'] = None
    state['managementState'] = 'normal'

    # Disable scanner-driven re-elevation
    state['autoSignalEnvironment'] = 'low'

    cursor.execute(
        'UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?',
        (json.dumps(state), bot_id),
    )
    updated += 1
    print(f"  Updated {bot_id} ({name}): threshold=5, manual mode")

conn.commit()
conn.close()
print(f"\nDone. {updated} bots updated in {DB_PATH}")
