import sqlite3
import json
conn = sqlite3.connect(r'C:\Users\zwexm\Downloads\zwesta_trading.db')
cursor = conn.cursor()

# Check runtime state for the bots that placed RIFUSDT trades
cursor.execute("SELECT bot_id, runtime_state FROM user_bots WHERE bot_id IN ('bot_1777235140561_7dc40c1b', 'bot_1777238322914')")
bots = cursor.fetchall()

print('Bot runtime states:')
for bot_id, runtime_state_json in bots:
    print(f'\nBot {bot_id}:')
    if runtime_state_json:
        try:
            runtime_state = json.loads(runtime_state_json)
            print(f'  Symbols: {runtime_state.get("symbols", [])}')
            print(f'  Current symbol: {runtime_state.get("current_symbol", "none")}')
            open_positions = runtime_state.get('open_positions', {})
            print(f'  Open positions: {len(open_positions)}')
            for ticket, pos in open_positions.items():
                print(f'    {ticket}: {pos.get("symbol")} {pos.get("type")} @ {pos.get("entryPrice")}')
        except json.JSONDecodeError:
            print(f'  Invalid JSON in runtime_state')
    else:
        print('  No runtime_state')

conn.close()