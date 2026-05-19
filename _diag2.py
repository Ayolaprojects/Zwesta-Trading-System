import sqlite3, json
DB = r'C:\backend\zwesta_trading.db'
c = sqlite3.connect(DB); cur = c.cursor()
cur.execute("SELECT bot_id, runtime_state FROM user_bots")
for r in cur.fetchall():
    bid, rs = r
    d = json.loads(rs) if rs else {}
    print(f'\n=== {bid} ===')
    for k in ('signalThreshold','effectiveSignalThreshold','adaptiveSignalThresholdOffset','adaptiveSignalThresholdReason',
              'maxOpenPositions','effectiveMaxOpenPositions','maxPositionsPerSymbol','effectiveMaxPositionsPerSymbol',
              'drawdownPauseUntil','drawdownPausePercent','drawdownPauseHours',
              'dailyProfit','maxDailyLoss','maxDrawdown',
              'accountBalance','accountEquity','riskPerTrade','basePositionSize',
              'autoAdaptationEnabled','intelligentScanner','autoSwitch',
              'managementMode','managementProfile','signalThresholdMode'):
        print(f'  {k}: {d.get(k)!r}')
    op = d.get('open_positions', {})
    print(f'  open_positions: {len(op)}')
    print(f'  symbolReentryCooldowns count: {len(d.get("symbolReentryCooldowns", {}))}')
    cd = d.get('symbolReentryCooldowns', {})
    for k, v in list(cd.items())[:5]:
        print(f'    cooldown {k}: {v}')
    lsr = d.get('lastScanResults')
    if lsr:
        print(f'  lastScanResults type: {type(lsr).__name__}')
        if isinstance(lsr, dict):
            print('   keys:', list(lsr.keys())[:10])
        elif isinstance(lsr, list) and lsr:
            print('   first:', str(lsr[0])[:200])
