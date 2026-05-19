import sqlite3, json
c = sqlite3.connect(r'C:\backend\zwesta_trading.db')
c.row_factory = sqlite3.Row
for r in c.execute("SELECT bot_id, runtime_state FROM user_bots WHERE broker_account_id LIKE 'Binance_%'").fetchall():
    s = json.loads(r['runtime_state'] or '{}')
    print(r['bot_id'], '| mode=', s.get('signalThresholdMode'), '| thr=', s.get('signalThreshold'),
          '| eff=', s.get('effectiveSignalThreshold'), '| autoSwitch=', s.get('autoSwitch'),
          '| openPos=', len(s.get('open_positions') or {}),
          '| profile=', s.get('botProfile'),
          '| ddPause=', s.get('drawdownPauseUntil'))
