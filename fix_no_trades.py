"""Clear ghost open_positions and restore effective caps for the 3 active bots.

Issue:
- runtime_state.open_positions has 8-12 stale tickets (entryTime 2026-04-26/27)
  but binance_orders table is empty -> these never reached Binance.
- effectiveMaxOpenPositions was forced to 2 (vs configured maxOpenPositions=4),
  so scanner skipped all signals because len(open_positions) >> cap.

Fix:
- Wipe open_positions
- Reset cycle counters / adaptive offsets / cooldowns
- Lift effectiveMaxOpenPositions to maxOpenPositions
- Clear drawdownPauseUntil
"""
import sqlite3, json, datetime
DB = r'C:\backend\zwesta_trading.db'
con = sqlite3.connect(DB)
cur = con.cursor()
cur.execute("SELECT bot_id, runtime_state FROM user_bots WHERE status='active' AND enabled=1")
rows = cur.fetchall()

for bid, rs in rows:
    d = json.loads(rs) if rs else {}
    before_open = len(d.get('open_positions') or {})
    d['open_positions'] = {}
    d['symbolReentryCooldowns'] = {}
    d['adaptiveSignalThresholdOffset'] = 0
    d['adaptiveSignalThresholdReason'] = None
    d['adaptiveSignalMissCount'] = 0
    # lift effective caps to configured
    cfg_max = int(d.get('maxOpenPositions') or 4)
    if cfg_max < 4:
        cfg_max = 4
        d['maxOpenPositions'] = 4
    d['effectiveMaxOpenPositions'] = cfg_max
    cfg_per = int(d.get('maxPositionsPerSymbol') or 1)
    d['effectiveMaxPositionsPerSymbol'] = cfg_per
    # ensure threshold actually 5
    d['signalThreshold'] = 5
    d['effectiveSignalThreshold'] = 5
    d['signalThresholdMode'] = 'manual'
    d['managementMode'] = 'assisted'
    # clear pauses
    d['drawdownPauseUntil'] = None
    d['dailyLossLimitHit'] = False
    d['emergencyStop'] = False
    # mark adaptation now so scanner re-runs
    d['lastAdaptationAt'] = datetime.datetime.utcnow().isoformat()
    new_rs = json.dumps(d)
    cur.execute(
        "UPDATE user_bots SET runtime_state=?, updated_at=? WHERE bot_id=?",
        (new_rs, datetime.datetime.utcnow().isoformat(), bid),
    )
    print(f'{bid}: cleared {before_open} ghost positions, effMax={cfg_max}, threshold=5')

con.commit()
con.close()
print('\nDone.')
