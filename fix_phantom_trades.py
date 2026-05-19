import sqlite3
import json
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Close the phantom RIFUSDT trades
cursor.execute('UPDATE trades SET status = "closed", time_close = datetime("now"), profit = 0.0 WHERE symbol = "RIFUSDT" AND status = "open"')
conn.commit()

# Remove from bot runtime states
cursor.execute('SELECT bot_id, runtime_state FROM user_bots WHERE bot_id IN ("bot_1777235140561_7dc40c1b", "bot_1777238322914")')
bots = cursor.fetchall()

for bot_id, runtime_state_json in bots:
    if runtime_state_json:
        try:
            runtime_state = json.loads(runtime_state_json)
            if 'open_positions' in runtime_state and 'SPOT-RIF' in runtime_state['open_positions']:
                del runtime_state['open_positions']['SPOT-RIF']
                updated_runtime = json.dumps(runtime_state)
                cursor.execute('UPDATE user_bots SET runtime_state = ? WHERE bot_id = ?', (updated_runtime, bot_id))
        except:
            pass

conn.commit()
conn.close()
print('Fixed phantom RIFUSDT trades')