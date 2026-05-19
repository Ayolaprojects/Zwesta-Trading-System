import sqlite3, json
DB = r'C:\backend\zwesta_trading.db'
c = sqlite3.connect(DB); cur = c.cursor()
cur.execute("SELECT bot_id, status, enabled, runtime_state, updated_at FROM user_bots")
for r in cur.fetchall():
    bid, st, en, rs, up = r
    try:
        d = json.loads(rs) if rs else {}
    except Exception as e:
        d = {'_parse_error': str(e)}
    print(f'\n=== {bid} | status={st} enabled={en} updated_at={up} ===')
    print('  managementMode:', d.get('managementMode'))
    print('  signalThreshold:', d.get('signalThreshold'))
    print('  managementProfile:', d.get('managementProfile'))
    print('  recoveryMode:', d.get('recoveryMode'))
    print('  lastAdaptationAt:', d.get('lastAdaptationAt'))
    op = d.get('open_positions', {})
    print('  open_positions count:', len(op))
    for k, v in list(op.items())[:5]:
        print(f'    {k}: sym={v.get("symbol")} type={v.get("type")} time_open={v.get("time_open")} entry={v.get("entry_price") or v.get("price")}')
    for k in ('paused','suspendUntil','tradingDisabled','blocked','riskBreached','dailyLossLimitHit','emergencyStop','maxOpenReached','tradingPaused','consecutiveLosses'):
        if k in d:
            print(f'  {k}:', d[k])
    print('  ALL keys:', sorted(list(d.keys()))[:60])
