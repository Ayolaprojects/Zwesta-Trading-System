import sqlite3
import json
conn = sqlite3.connect('zwesta_trading.db')
cursor = conn.cursor()
cursor.execute("SELECT bot_id, runtime_state FROM bots")
bots = cursor.fetchall()
print('Bot runtime states:')
for bot_id, runtime_state_json in bots:
    if runtime_state_json:
        try:
            runtime_state = json.loads(runtime_state_json)
            open_positions = runtime_state.get('open_positions', [])
            print(f'Bot {bot_id}: {len(open_positions)} open positions')
            for pos in open_positions:
                print(f'  Symbol: {pos.get("symbol")}, Status: {pos.get("status")}, Ticket: {pos.get("ticket")}')
        except json.JSONDecodeError:
            print(f'Bot {bot_id}: Invalid JSON in runtime_state')
    else:
        print(f'Bot {bot_id}: No runtime_state')
conn.close()