import sqlite3
import json
from runtime_infrastructure import get_database_path

path = get_database_path()
print('DBPATH:', path)
conn = sqlite3.connect(path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
for bot_id in ['1780678113048', '178090663839']:
    print('\nBOT', bot_id)
    cur.execute(
        'SELECT bot_id, user_id, name, status, enabled, daily_profit, total_profit, runtime_state, created_at, updated_at FROM user_bots WHERE bot_id = ?',
        (bot_id,),
    )
    row = cur.fetchone()
    if not row:
        print('  NOT FOUND in user_bots')
        continue
    print('  bot_id', row['bot_id'])
    print('  name', row['name'])
    print('  status', row['status'])
    print('  enabled', row['enabled'])
    print('  daily_profit', row['daily_profit'])
    print('  total_profit', row['total_profit'])
    print('  created_at', row['created_at'])
    print('  updated_at', row['updated_at'])
    print('  runtime_state_present', bool(row['runtime_state']))
    if row['runtime_state']:
        try:
            data = json.loads(row['runtime_state'])
            print('  runtime totalProfit', data.get('totalProfit'), 'dailyProfit', data.get('dailyProfit'))
            print('  runtime tradeHistory len', len(data.get('tradeHistory') or []))
            print('  runtime dailyProfits keys', list((data.get('dailyProfits') or {}).keys())[:5])
        except Exception as e:
            print('  runtime parse error', e)
    cur.execute(
        'SELECT COUNT(*) AS cnt, SUM(profit) AS sum_profit FROM trades WHERE bot_id = ? AND status = "closed"',
        (bot_id,),
    )
    tr = cur.fetchone()
    print('  closed trades count', tr['cnt'], 'closed profit sum', tr['sum_profit'])
    cur.execute('SELECT COUNT(*) AS cnt FROM trades WHERE bot_id = ? AND status = "open"', (bot_id,))
    op = cur.fetchone()
    print('  open trades count', op['cnt'])
conn.close()
