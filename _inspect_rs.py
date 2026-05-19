import sqlite3, json
c = sqlite3.connect(r'C:\backend\zwesta_trading.db')
c.row_factory = sqlite3.Row
for r in c.execute("SELECT bot_id, runtime_state FROM user_bots"):
    rs = json.loads(r['runtime_state'] or '{}')
    print(r['bot_id'])
    for k in ('signalThresholdMode','signalThreshold','effectiveSignalThreshold','maxOpenPositions','managementMode','drawdownPauseUntil','autoSwitch','allowAdaptiveRawFallback','intelligentScanner','autoAdaptationEnabled','peakProfit','maxDrawdown','accountEquityHighWatermark'):
        print(f"  {k}={rs.get(k)!r}")
